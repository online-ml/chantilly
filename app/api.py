import copy
import json
import queue

import creme.base
import creme.utils.estimator_checks
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
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg


@bp.route('/model', methods=['GET', 'POST'])
def model():

    # POST: set the model
    if flask.request.method == 'POST':
        model = dill.loads(flask.request.get_data())
        try:
            db.set_model(model, reset_metrics=flask.request.args.get('reset_metrics', True))
        except ValueError as err:
            raise exceptions.InvalidUsage(message=str(err))
        return {}, 201

    # GET: return the current model
    shelf = db.get_shelf()
    model = shelf['model']
    return dill.dumps(model)


class PredictSchema(mm.Schema):
    features = mm.fields.Dict(required=True)
    id = mm.fields.Raw()  # as long as it can be coerced to a str it's okay


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
        model = shelf['model']
    except KeyError:
        raise exceptions.InvalidUsage(message='You first need to provide a model.')

    # We make a copy because the model might modify the features in-place
    features = copy.deepcopy(payload['features'])

    # Make the prediction
    if hasattr(creme.utils.estimator_checks.guess_model(model), 'predict_proba_one'):
        pred = model.predict_proba_one(x=features)
    else:
        pred = model.predict_one(x=features)

    # Announce the prediction
    msg = json.dumps({'features': payload['features'], 'prediction': pred})
    EVENTS_ANNOUNCER.announce(format_sse(data=msg, event='predict'))

    # If an ID is provided, then we store the features in order to be able to use them for learning
    # further down the line.
    status_code = 200
    if 'id' in payload:
        shelf['#%s' % payload['id']] = {
            'features': payload['features'],
            'prediction': pred
        }
        status_code = 201

    return {'prediction': pred}, status_code


class LearnSchema(mm.Schema):
    features = mm.fields.Dict()
    id = mm.fields.Raw()
    ground_truth = mm.fields.Raw(required=True)


@bp.route('/learn', methods=['POST'])
def learn():

    # Validate the payload
    try:
        schema = LearnSchema()
        payload = schema.load(flask.request.json)
    except mm.ValidationError as err:
        raise exceptions.InvalidUsage(message=err.normalized_messages())

    # Load the model
    shelf = db.get_shelf()
    try:
        model = shelf['model']
    except KeyError:
        raise exceptions.InvalidUsage(message='You first need to provide a model.')

    # If an ID is given, then check if any associated features and prediction are stored
    features = payload.get('features')
    prediction = None
    if 'id' in payload:
        memory = shelf.get('#%s' % payload['id'], {})
        features = memory.get('features')
        prediction = memory.get('prediction')

    # Raise an error if no features are provided
    if features is None:
        raise exceptions.InvalidUsage('No features are stored and none were provided.')

    # Obtain a prediction if none was made earlier
    if prediction is None:
        prediction = model.predict_proba_one(features)

    # Update the metric
    metrics = shelf['metrics']
    for metric in metrics:
        # If the metrics requires labels but prediction is a dict, then we need to retrieve the
        # predicted label with the highest probability
        if metric.requires_labels and isinstance(prediction, dict):
            # At this point prediction is a dict, but it might be empty because no training data
            # has been seen
            if len(prediction) == 0:
                continue
            pred = max(prediction, key=prediction.get)
            metric.update(y_true=payload['ground_truth'], y_pred=pred)
        else:
            metric.update(y_true=payload['ground_truth'], y_pred=prediction)
    shelf['metrics'] = metrics

    msg = json.dumps({
        'features': features,
        'prediction': prediction,
        'ground_truth': payload['ground_truth']
    })
    EVENTS_ANNOUNCER.announce(format_sse(data=msg, event='learn'))

    # Announce the current metric values
    msg = json.dumps({metric.__class__.__name__: metric.get() for metric in metrics})
    METRICS_ANNOUNCER.announce(format_sse(data=msg))

    # Update the model
    model.fit_one(x=features, y=payload['ground_truth'])
    shelf['model'] = model

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
