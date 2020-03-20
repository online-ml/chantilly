import copy
import json
import queue

import creme.base
import creme.utils.estimator_checks
import flask
import dill

from . import db


bp = flask.Blueprint('api', __name__, url_prefix='/api')

queue = queue.Queue()

@bp.route('/predict', methods=['POST'])
def predict():

    payload = flask.request.json

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


@bp.route('/learn', methods=['POST'])
def learn():

    payload = flask.request.json
    shelf = db.get_shelf()

    # If an ID is given, then check if any associated features and prediction are stored
    features = None
    prediction = None
    if 'id' in payload:
        memory = shelf.get('#%s' % payload['id'], {})
        features = memory.get('features')
        prediction = memory.get('prediction')

    # If features are provided in the request, then they have precedence
    if 'features' in payload:
        features = payload['features']

    # Raise an error if no features are provided
    if features is None:
        raise ValueError('No features are stored and none were provided')

    # Obtain a prediction if none was made earlier
    model = shelf['model']
    if prediction is None:
        prediction = model.predict_proba_one(features)

    # Update the metric
    metrics = shelf['metrics']
    for metric in metrics:
        metric.update(y_true=payload['target'], y_pred=prediction)
    shelf['metrics'] = metrics

    queue.put({
        metric.__class__.__name__: metric.get()
        for metric in metrics
    })

    # Update the model
    model.fit_one(x=features, y=payload['target'])
    shelf['model'] = model

    return {}, 201


@bp.route('/model', methods=['GET', 'POST'])
def set_model():
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
    metrics = shelf['metrics']

    return {
        metric.__class__.__name__: metric.get()
        for metric in metrics
    }


@bp.route('/metric-updates')
def metric_updates():
    def updates():
        while True:
            metrics = queue.get()  # blocks while queue is empty
            yield f'data: {json.dumps(metrics)}\n\n'
    return flask.Response(updates(), mimetype='text/event-stream')
