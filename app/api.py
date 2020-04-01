import copy
import json
import queue

from creme.metrics.base import ClassificationMetric
import dill
import flask
import marshmallow as mm

from . import db
from . import exceptions


bp = flask.Blueprint('api', __name__, url_prefix='/api')


class MessageAnnouncer:

    def __init__(self):
        self.listeners = []

    def listen(self):
        self.listeners.append(queue.Queue(maxsize=1))
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


class InitSchema(mm.Schema):
    flavor = mm.fields.Str(required=True)


@bp.route('/init', methods=['GET', 'POST'])
def init():

    # GET: return the current configuration
    if flask.request.method == 'GET':
        shelf = db.get_shelf()
        try:
            flavor = shelf['flavor']
        except KeyError:
            raise exceptions.InvalidUsage(message='No flavor has been set.')
        return {'flavor': flavor.name}

    # POST: configure chantilly

    # Validate the payload
    try:
        schema = InitSchema()
        payload = schema.load(flask.request.json)
    except mm.ValidationError as err:
        raise exceptions.InvalidUsage(message=err.normalized_messages())

    # Set the flavor
    try:
        db.set_flavor(flavor=payload['flavor'])
    except exceptions.UnknownFlavor as err:
        raise exceptions.InvalidUsage(message=str(err))

    return {}, 201


@bp.route('/model', methods=['GET', 'POST'])
@bp.route('/model/<name>', methods=['GET', 'POST', 'DELETE'])
def model(name=None):

    shelf = db.get_shelf()

    # DELETE: drop the model
    if flask.request.method == 'DELETE':
        key = f'models/{name}'
        if key not in shelf:
            return {}, 404
        del shelf[key]
        return {}, 204

    # POST: set the model
    if flask.request.method == 'POST':
        model = dill.loads(flask.request.get_data())

        # Validate the model
        try:
            flavor = shelf['flavor']
        except KeyError:
            raise exceptions.InvalidUsage(message='No flavor has been set.')
        ok, error = flavor.check_model(model)
        if not ok:
            raise exceptions.InvalidUsage(message=error)
        name = db.add_model(model, name=name)
        shelf['default_model_name'] = name  # the most recent model becomes the default
        return {'name': name}, 201

    # GET: return the current model
    name = shelf['default_model_name'] if name is None else name
    model = shelf[f'models/{name}']
    return dill.dumps(model)


@bp.route('/models', methods=['GET'])
def models():
    shelf = db.get_shelf()
    model_names = [k.split('/', 1)[1] for k in shelf if k.startswith('models/')]
    return {'models': model_names, 'default': shelf.get('default_model_name')}, 200


class PredictSchema(mm.Schema):
    features = mm.fields.Dict(required=True)
    id = mm.fields.Raw()  # as long as it can be coerced to a str it's okay
    model = mm.fields.Str()


@bp.route('/predict', methods=['POST'])
def predict():

    # Validate the payload
    try:
        schema = PredictSchema()
        payload = schema.load(flask.request.json)
    except mm.ValidationError as err:
        raise exceptions.InvalidUsage(message=err.normalized_messages())

    # Load the model
    shelf = db.get_shelf()
    try:
        default_model_name = shelf['default_model_name']
    except KeyError:
        raise exceptions.InvalidUsage(message='No default model has been set.')
    model_name = payload.get('model', default_model_name)
    try:
        model = shelf[f'models/{model_name}']
    except KeyError:
        raise exceptions.InvalidUsage(message=f"No model named '{model_name}'.")

    # We make a copy because the model might modify the features in-place while we want to be able
    # to store an identical copy
    features = copy.deepcopy(payload['features'])

    # Make the prediction
    flavor = shelf['flavor']
    pred_func = getattr(model, flavor.pred_func)
    try:
        pred = pred_func(x=features)
    except Exception as e:
        raise exceptions.InvalidUsage(message=str(e))

    # The unsupervised parts of the model might be updated after a prediction, so we need to store
    # it
    shelf[f'models/{model_name}'] = model

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
        shelf['#%s' % payload['id']] = {
            'model': model_name,
            'features': payload['features'],
            'prediction': pred
        }
        status_code = 201

    return {'model': model_name, 'prediction': pred}, status_code


class LearnSchema(mm.Schema):
    features = mm.fields.Dict()
    id = mm.fields.Raw()
    ground_truth = mm.fields.Raw(required=True)
    model = mm.fields.Str()


@bp.route('/learn', methods=['POST'])
def learn():

    # Validate the payload
    try:
        schema = LearnSchema()
        payload = schema.load(flask.request.json)
    except mm.ValidationError as err:
        raise exceptions.InvalidUsage(message=err.normalized_messages())

    # If an ID is given, then retrieve the stored info.
    shelf = db.get_shelf()
    try:
        memory = shelf['#%s' % payload['id']] if 'id' in payload else {}
    except KeyError:
        raise exceptions.InvalidUsage(message=f"No information stored for ID '{payload['id']}'.")
    model_name = memory.get('model')
    features = memory.get('features')
    prediction = memory.get('prediction')

    # Override with the information provided in the request
    model_name = payload.get('model', model_name)
    features = payload.get('features', features)
    prediction = payload.get('prediction', prediction)

    # Load the model
    if model_name is None:
        try:
            default_model_name = shelf['default_model_name']
        except KeyError:
            raise exceptions.InvalidUsage(message='No default model has been set.')
        model_name = default_model_name
    try:
        model = shelf[f'models/{model_name}']
    except KeyError:
        raise exceptions.InvalidUsage(message=f"No model named '{model_name}'.")

    # Raise an error if no features are provided
    if features is None:
        raise exceptions.InvalidUsage(message='No features are stored and none were provided.')

    # Obtain a prediction if none was made earlier
    if prediction is None:
        flavor = shelf['flavor']
        pred_func = getattr(model, flavor.pred_func)
        try:
            prediction = pred_func(x=copy.deepcopy(features))
        except Exception as e:
            raise exceptions.InvalidUsage(message=str(e))

    # Update the metrics
    metrics = shelf['metrics']
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
    shelf['metrics'] = metrics

    # Update the model
    try:
        model.fit_one(x=copy.deepcopy(features), y=payload['ground_truth'])
    except Exception as e:
        raise exceptions.InvalidUsage(message=str(e))
    shelf[f'models/{model_name}'] = model

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

    # Delete the payload from the shelf
    if 'id' in payload:
        try:
            del shelf['#%s' % payload['id']]
        except KeyError:
            pass

    return {}, 201


@bp.route('/metrics', methods=['GET'])
def metrics():
    shelf = db.get_shelf()
    return {metric.__class__.__name__: metric.get() for metric in shelf['metrics']}


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
