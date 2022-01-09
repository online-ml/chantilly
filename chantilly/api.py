import copy
import json
import queue
import time

import cerberus
import river
from river.metrics.base import ClassificationMetric
import dill
import flask

from . import exceptions
from . import storage


bp = flask.Blueprint('api', __name__, url_prefix='/api')


class MessageAnnouncer:

    def __init__(self):
        self.listeners = []

    def listen(self):
        self.listeners.append(queue.Queue(maxsize=10))
        return self.listeners[-1]

    def announce(self, msg):
        # TODO: there's probably a better way to deal with listeners that aren't listening anymore
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]


METRICS_ANNOUNCER = MessageAnnouncer()

EVENTS_ANNOUNCER = MessageAnnouncer()


def format_sse(data: str, event=None) -> str:
    """

    >>> format_sse(data=json.dumps({'abc': 123}), event='Jackson 5')
    'event: Jackson 5\\ndata: {"abc": 123}\\n\\n'

    """
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg


@bp.before_request
def before_request_func():
    if flask.request.endpoint in ('api.learn', 'api.predict'):
        flask.request.started_at = time.perf_counter_ns()


@bp.after_request
def after_request_func(response):

    if flask.request.endpoint not in ('api.learn', 'api.predict'):
        return response

    duration = time.perf_counter_ns() - flask.request.started_at
    db = storage.get_db()
    stats = db['stats']

    if flask.request.endpoint == 'api.learn':
        stats['learn_mean'].update(duration)
        stats['learn_ewm'].update(duration)
    elif flask.request.endpoint == 'api.predict':
        stats['predict_mean'].update(duration)
        stats['predict_ewm'].update(duration)

    db['stats'] = stats
    return response


InitSchema = {
    'flavor': {'type': 'string', 'required': True},
}


@bp.route('/init', methods=['GET', 'POST'])
def init():

    # GET: return the current configuration
    if flask.request.method == 'GET':
        db = storage.get_db()
        try:
            flavor = db['flavor']
        except KeyError:
            raise exceptions.FlavorNotSet

        return {
            'flavor': flavor.name,
            'storage': flask.current_app.config['STORAGE_BACKEND'],
            'river_version': river.__version__
        }

    # POST: configure chantilly

    # Validate the payload
    payload = flask.request.json
    v = cerberus.Validator(InitSchema)
    ok = v.validate(payload)
    if not ok:
        raise exceptions.InvalidUsage(message=v.errors)

    # Set the flavor
    try:
        storage.set_flavor(flavor=payload['flavor'])
    except exceptions.UnknownFlavor as err:
        raise exceptions.InvalidUsage(message=str(err))

    return {}, 201


@bp.route('/model', methods=['GET', 'POST'])
@bp.route('/model/<name>', methods=['GET', 'POST', 'DELETE'])
def model(name=None):

    db = storage.get_db()

    # DELETE: drop the model
    if flask.request.method == 'DELETE':
        key = f'models/{name}'
        if key not in db:
            return {}, 404
        del db[key]
        return {}, 204

    # POST: set the model
    if flask.request.method == 'POST':
        model = dill.loads(flask.request.get_data())

        # Validate the model
        try:
            flavor = db['flavor']
        except KeyError:
            raise exceptions.FlavorNotSet

        ok, error = flavor.check_model(model)
        if not ok:
            raise exceptions.InvalidUsage(message=error)
        name = storage.add_model(model, name=name)
        db['default_model_name'] = name  # the most recent model becomes the default
        return {'name': name}, 201

    # GET: return the current model
    name = db['default_model_name'] if name is None else name
    model = db[f'models/{name}']
    return dill.dumps(model)


@bp.route('/models', methods=['GET'])
def models():
    db = storage.get_db()
    model_names = sorted([k.split('/', 1)[1] for k in db if k.startswith('models/')])
    return {'models': model_names, 'default': db.get('default_model_name')}, 200


PredictSchema = {
    'features': {'anyof': [{'type': 'dict'}, {'type': 'string'}], 'required': True},
    'id': {'anyof': [{'type': 'integer'}, {'type': 'string'}]},
    'model': {'type': 'string'},
}


@bp.route('/predict', methods=['POST'])
def predict():

    # Validate the payload
    payload = flask.request.json
    v = cerberus.Validator(PredictSchema)
    ok = v.validate(payload)
    if not ok:
        raise exceptions.InvalidUsage(message=v.errors)

    # Load the model
    db = storage.get_db()
    try:
        default_model_name = db['default_model_name']
    except KeyError:
        raise exceptions.InvalidUsage(message='No default model has been set.')

    model_name = payload.get('model', default_model_name)
    try:
        model = db[f'models/{model_name}']
    except KeyError:
        raise exceptions.InvalidUsage(message=f"No model named '{model_name}'.")

    # We make a copy because the model might modify the features in-place while we want to be able
    # to store an identical copy
    features = copy.deepcopy(payload['features'])

    # Make the prediction
    flavor = db['flavor']
    pred_func = getattr(model, flavor.pred_func)
    try:
        pred = pred_func(x=features)
    except Exception as e:
        raise exceptions.InvalidUsage(message=repr(e))

    # The unsupervised parts of the model might be updated after a prediction, so we need to store
    # it
    db[f'models/{model_name}'] = model

    # Announce the prediction
    if EVENTS_ANNOUNCER.listeners:
        EVENTS_ANNOUNCER.announce(format_sse(
            data=json.dumps({
                'model': model_name,
                'features': payload['features'],
                'prediction': pred
            }),
            event='predict'
        ))

    # If an ID is provided, then we store the features in order to be able to use them for learning
    # further down the line.
    status_code = 200
    if 'id' in payload:
        db['#%s' % payload['id']] = {
            'model': model_name,
            'features': payload['features'],
            'prediction': pred
        }
        status_code = 201

    return {'model': model_name, 'prediction': pred}, status_code


LearnSchema = {
    'features': {'anyof': [{'type': 'dict'}, {'type': 'string'}]},
    'id': {'anyof': [{'type': 'integer'}, {'type': 'string'}]},
    'ground_truth': {'required': True},
    'model': {'type': 'string'},
}


@bp.route('/learn', methods=['POST'])
def learn():

    # Validate the payload
    payload = flask.request.json
    v = cerberus.Validator(LearnSchema)
    ok = v.validate(payload)
    if not ok:
       raise exceptions.InvalidUsage(message=v.errors)

    # Unpack the information provided in the request
    model_name = payload.get('model')
    features = payload.get('features')
    prediction = payload.get('prediction')

    # If an ID is given, then retrieve the stored info.
    db = storage.get_db()
    try:
        memory = db['#%s' % payload['id']] if 'id' in payload else {}
    except KeyError:
        raise exceptions.InvalidUsage(message=f"No information stored for ID '{payload['id']}'.")
    model_name = memory.get('model', model_name)
    features = memory.get('features', features)
    prediction = memory.get('prediction', prediction)

    # Raise an error if no features are provided
    if features is None:
        raise exceptions.InvalidUsage(message='No features are stored and none were provided.')

    # Load the model
    if model_name is None:
        try:
            default_model_name = db['default_model_name']
        except KeyError:
            raise exceptions.InvalidUsage(message='No default model has been set.')
        model_name = default_model_name
    try:
        model = db[f'models/{model_name}']
    except KeyError:
        raise exceptions.InvalidUsage(message=f"No model named '{model_name}'.")

    # Obtain a prediction if none was made earlier
    if prediction is None:
        flavor = db['flavor']
        pred_func = getattr(model, flavor.pred_func)
        try:
            prediction = pred_func(x=copy.deepcopy(features))
        except Exception as e:
            raise exceptions.InvalidUsage(message=repr(e))

    # Update the metrics
    metrics = db['metrics']
    for metric in metrics:
        # If the metrics requires labels but the prediction is a dict, then we need to retrieve the
        # predicted label with the highest probability
        if (
            isinstance(metric, ClassificationMetric) and
            metric.requires_labels and
            isinstance(prediction, dict)
        ):
            # At this point prediction is a dict, but it might be empty because no training data
            # has been seen
            if len(prediction) == 0:
                continue
            pred = max(prediction, key=prediction.get)
            metric.update(y_true=payload['ground_truth'], y_pred=pred)
        else:
            metric.update(y_true=payload['ground_truth'], y_pred=prediction)
    db['metrics'] = metrics

    # Update the model
    try:
        model.learn_one(x=copy.deepcopy(features), y=payload['ground_truth'])
    except Exception as e:
        raise exceptions.InvalidUsage(message=repr(e))
    db[f'models/{model_name}'] = model

    # Announce the event
    if EVENTS_ANNOUNCER.listeners:
        EVENTS_ANNOUNCER.announce(format_sse(
            data=json.dumps({
                'model': model_name,
                'features': features,
                'prediction': prediction,
                'ground_truth': payload['ground_truth']
            }),
            event='learn'
        ))

    # Announce the current metric values
    if METRICS_ANNOUNCER.listeners:
        msg = json.dumps({metric.__class__.__name__: metric.get() for metric in metrics})
        METRICS_ANNOUNCER.announce(format_sse(data=msg))

    # Delete the payload from the db
    if 'id' in payload:
        try:
            del db['#%s' % payload['id']]
        except KeyError:
            pass

    return {}, 201


@bp.route('/metrics', methods=['GET'])
def metrics():
    db = storage.get_db()
    try:
        metrics = db['metrics']
    except KeyError:
        raise exceptions.FlavorNotSet

    return {metric.__class__.__name__: metric.get() for metric in metrics}


@bp.route('/stream/metrics', methods=['GET'])
def stream_metrics():
    def stream():
        messages = METRICS_ANNOUNCER.listen()
        while True:
            metrics = messages.get()  # blocks until a new message arrives
            yield metrics
    return flask.Response(stream(), mimetype='text/event-stream')


@bp.route('/stream/events', methods=['GET'])
def stream_events():
    def stream():
        messages = EVENTS_ANNOUNCER.listen()
        while True:
            event = messages.get()  # blocks until a new message arrives
            yield event
    return flask.Response(stream(), mimetype='text/event-stream')


def humanize_ns(ns: int) -> str:

    if ns == 0:
        return '0ns'

    μs = ('μs', 1000)
    ms = ('ms', μs[1] * 1000)
    s  = ('s',  ms[1] * 1000)
    m  = ('m',   s[1] * 60)

    rep = ''

    for d in (m, s, ms, μs):
        k, ns = divmod(ns, d[1])
        if k:
            rep += f'{k}{d[0]}'

    if ns:
        rep += f'{ns}ns'

    return rep


@bp.route('/stats', methods=['GET'])
def stats():
    db = storage.get_db()
    try:
        stats = db['stats']
    except KeyError:
        raise exceptions.InvalidUsage(message='No flavor has been set.')
    return {
        'predict': {
            'n_calls': int(stats['predict_mean'].n),
            'mean_duration': int(stats['predict_mean'].get()),
            'mean_duration_human': humanize_ns(int(stats['predict_mean'].get())),
            'ewm_duration': int(stats['predict_ewm'].get()),
            'ewm_duration_human': humanize_ns(int(stats['predict_ewm'].get()))
        },
        'learn': {
            'n_calls': int(stats['learn_mean'].n),
            'mean_duration': int(stats['learn_mean'].get()),
            'mean_duration_human': humanize_ns(int(stats['learn_mean'].get())),
            'ewm_duration': int(stats['learn_ewm'].get()),
            'ewm_duration_human': humanize_ns(int(stats['learn_ewm'].get()))
        }
    }
