import flask

from . import db


bp = flask.Blueprint('api', __name__, url_prefix='/api')


@bp.route('/predict', methods=['POST'])
def predict():

    payload = flask.request.json

    # Load the model
    shelf = db.get_shelf()
    model = shelf['model']
    pred = model.predict_one(payload['features'])

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
        e = shelf.get('#%s' % payload['id'], {})
        features = e.get('features')
        prediction = e.get('prediction')

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
    metric = shelf['metric']
    metric.update(payload['target'], prediction)
    shelf['metric'] = metric

    # Update the model
    model.fit_one(features, payload['target'])
    shelf['model'] = model

    return {}, 201

