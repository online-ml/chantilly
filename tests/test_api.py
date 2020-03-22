import json
import pickle
import pytest
import uuid

from creme import tree

from app import db
from app import exceptions



@pytest.fixture
def model_fixture(client):
    client.post('/api/model', data=pickle.dumps(tree.DecisionTreeClassifier()))


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


def test_predict(client, app, model_fixture):
    r = client.post('/api/predict',
        data=json.dumps({'features': {}}),
        content_type='application/json'
    )
    assert r.status_code == 200
    assert 'prediction' in r.json


def test_predict_with_id(client, app, model_fixture):

    r = client.post('/api/predict',
        data=json.dumps({'features': {}, 'id': '90210'}),
        content_type='application/json'
    )
    assert r.status_code == 201
    assert 'prediction' in r.json

    with app.app_context():
        shelf = db.get_shelf()
        assert '#90210' in shelf


def test_predict_no_features(client, app, model_fixture):
    with pytest.raises(exceptions.InvalidUsage):
        client.post('/api/predict',
            data=json.dumps({'id': 42}),
            content_type='application/json'
        )


def test_learn(client, app, model_fixture):

    r = client.post('/api/learn',
        data=json.dumps({'features': {'x': 1}, 'ground_truth': True}),
        content_type='application/json'
    )
    assert r.status_code == 201

    with app.app_context():
        for metric in db.get_shelf()['metrics']:
            assert metric.n == 1


def test_learn_with_id(client, app, model_fixture):

    client.post('/api/predict',
        data=json.dumps({'id': 42, 'features': {'x': 1}}),
        content_type='application/json'
    )

    r = client.post('/api/learn',
        data=json.dumps({'id': 42, 'ground_truth': True}),
        content_type='application/json'
    )
    assert r.status_code == 201

    with app.app_context():
        for metric in db.get_shelf()['metrics']:
            assert metric.n == 1


def test_learn_no_ground_truth(client, app, model_fixture):
    with pytest.raises(exceptions.InvalidUsage):
        client.post('/api/learn',
            data=json.dumps({'features': {'x': 1}}),
            content_type='application/json'
        )


def test_learn_no_features(client, app, model_fixture):
    with pytest.raises(exceptions.InvalidUsage):
        client.post('/api/learn',
            data=json.dumps({'ground_truth': True}),
            content_type='application/json'
        )
