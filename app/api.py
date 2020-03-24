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

    def annouce(self, msg):
        # TODO: there's probably a better way to deal with listeners that aren't listening anymore
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]

METRICS_ANNOUNCER = MessageAnnouncer()


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
        raise exceptions.InvalidUsage(err)

    # We make a copy because the model might modify the features in-place
    features = copy.deepcopy(payload['features'])

    # Load the model
    shelf = db.get_shelf()
    model = shelf['model']
    if isinstance(creme.utils.estimator_checks.guess_model(model), creme.base.Classifier):
        pred = model.predict_proba_one(x=features)
    else:
        pred = model.predict_one(x=features)

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
        raise exceptions.InvalidUsage(err)

    # If an ID is given, then check if any associated features and prediction are stored
    features = payload.get('features')
    prediction = None
    shelf = db.get_shelf()
    if 'id' in payload:
        memory = shelf.get('#%s' % payload['id'], {})
        features = memory.get('features')
        prediction = memory.get('prediction')

    # Raise an error if no features are provided
    if features is None:
        raise exceptions.InvalidUsage('No features are stored and none were provided')

    # Obtain a prediction if none was made earlier
    model = shelf['model']
    if prediction is None:
        prediction = model.predict_proba_one(features)

    # Update the metric
    metrics = shelf['metrics']
    for metric in metrics:
        metric.update(y_true=payload['ground_truth'], y_pred=prediction)
    shelf['metrics'] = metrics

    # Push the current metric values into the queue
    msg = {metric.__class__.__name__: metric.get() for metric in metrics}
    METRICS_ANNOUNCER.annouce(msg)

    # Update the model
    model.fit_one(x=features, y=payload['ground_truth'])
    shelf['model'] = model

    return {}, 201


@bp.route('/model', methods=['GET', 'POST'])
def model():
    if flask.request.method == 'POST':
        model = dill.loads(flask.request.get_data())
        db.set_model(model, reset_metrics=flask.request.args.get('reset_metrics', True))
        return {}, 201

    shelf = db.get_shelf()
    model = shelf['model']
    return dill.dumps(model)


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
            yield f'data: {json.dumps(metrics)}\n\n'
    return flask.Response(stream(), mimetype='text/event-stream')
