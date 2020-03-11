import json
import pickle
import uuid

from creme import tree

from app import db


def test_predict(client, app):

    r = client.post(
        '/api/predict',
        data=json.dumps({'features': {}}),
        content_type='application/json'
    )
    assert r.status_code == 200
    assert 'prediction' in r.json


def test_predict_with_id(client, app):

    r = client.post(
        '/api/predict',
        data=json.dumps({'features': {}, 'id': '90210'}),
        content_type='application/json'
    )
    assert r.status_code == 201
    assert 'prediction' in r.json

    with app.app_context():
        shelf = db.get_shelf()
        assert '#90210' in shelf


def test_learn(client, app):

    r = client.post(
        '/api/learn',
        data=json.dumps({'features': {'x': 1}, 'target': True}),
        content_type='application/json'
    )
    assert r.status_code == 201

    with app.app_context():
        for metric in db.get_shelf()['metrics']:
            assert metric.n == 1
        if not app.config['API_ONLY']:
            assert len(db.get_influx().query('SELECT * FROM scores;')) == 1


def test_learn_with_id(client, app):

    client.post(
        '/api/predict',
        data=json.dumps({'id': 42, 'features': {'x': 1}}),
        content_type='application/json'
    )

    r = client.post(
        '/api/learn',
        data=json.dumps({'id': 42, 'target': True}),
        content_type='application/json'
    )
    assert r.status_code == 201

    with app.app_context():
        for metric in db.get_shelf()['metrics']:
            assert metric.n == 1
        if not app.config['API_ONLY']:
            assert len(db.get_influx().query('SELECT * FROM scores;')) == 1


def test_model(client, app):

    # Instantiate a model
    model = tree.DecisionTreeClassifier()
    probe = uuid.uuid4()
    model.probe = probe

    # Upload the model
    client.post('/api/model', data=pickle.dumps(model))

    # Check that the model has been added to the shelf
    with app.app_context():
        shelf = db.get_shelf()
        assert isinstance(shelf['model'], tree.DecisionTreeClassifier)
        assert shelf['model'].probe == probe

    # Check that the model can be retrieved via the API
    model = pickle.loads(client.get('/api/model').get_data())
    assert isinstance(model, tree.DecisionTreeClassifier)
    assert model.probe == probe
