import json
import pickle
import pytest
import uuid

from creme import linear_model
from creme import tree

from app import db
from app import exceptions


@pytest.fixture
def regression(client):
    client.post('/api/init',
        data=json.dumps({'flavor': 'regression'}),
        content_type='application/json'
    )


@pytest.fixture
def lin_reg(client):
    client.post('/api/model/lin-reg', data=pickle.dumps(linear_model.LinearRegression()))


def test_init_bad_flavor(client, app):
    r = client.post('/api/init',
        data=json.dumps({'flavor': 'zugzug'}),
        content_type='application/json'
    )
    assert r.status_code == 400
    assert r.json == {'message': "Allowed flavors are 'regression', 'binary', 'multiclass'."}


def test_init(client, app):
    r = client.post('/api/init',
        data=json.dumps({'flavor': 'regression'}),
        content_type='application/json'
    )
    assert r.status_code == 201

    with app.app_context():
        assert db.get_shelf()['flavor'].name == 'regression'


class ModelWithoutFit:
    def predict_one(self, x):
        return True

def test_model_without_fit(client, app, regression):
    r = client.post('/api/model', data=pickle.dumps(ModelWithoutFit()))
    assert r.json == {'message': 'The model does not implement fit_one.'}


class ModelWithoutPredict:
    def fit_one(self, x, y):
        return self

def test_model_without_predict(client, app, regression):
    r = client.post('/api/model', data=pickle.dumps(ModelWithoutPredict()))
    assert r.json == {'message': 'The model does not implement predict_one.'}


def test_model_upload(client, app, regression):

    # Instantiate a model
    model = linear_model.LinearRegression()
    probe = uuid.uuid4()
    model.probe = probe

    # Upload the model
    r = client.post('/api/model/healthy-banana', data=pickle.dumps(model))
    assert r.status_code == 201
    assert r.json == {'name': 'healthy-banana'}

    # Check that the model has been added to the shelf
    with app.app_context():
        shelf = db.get_shelf()
        assert isinstance(shelf['models/healthy-banana'], linear_model.LinearRegression)
        assert shelf['models/healthy-banana'].probe == probe

    # Check that the model can be retrieved via the API with it's name
    model = pickle.loads(client.get('/api/model/healthy-banana').get_data())
    assert isinstance(model, linear_model.LinearRegression)
    assert model.probe == probe

    # Check that the model can be retrieved via the API by default
    model = pickle.loads(client.get('/api/model').get_data())
    assert isinstance(model, linear_model.LinearRegression)
    assert model.probe == probe


def test_model_delete(client, app, regression):

    # Upload a model
    model = linear_model.LinearRegression()
    client.post('/api/model/healthy-banana', data=pickle.dumps(model))

    with app.app_context():
        assert 'models/healthy-banana' in db.get_shelf()

    # Delete it
    client.delete('/api/model/healthy-banana')

    with app.app_context():
        assert 'models/healthy-banana' not in db.get_shelf()


def test_predict_no_model(client, app, regression):
    r = client.post('/api/predict',
        data=json.dumps({'features': {}}),
        content_type='application/json'
    )
    assert r.json == {'message': 'No default model has been set.'}


def test_predict_no_features(client, app, regression, lin_reg):
    r = client.post('/api/predict',
        data=json.dumps({'id': 42}),
        content_type='application/json'
    )
    assert r.json == {'message': {'features': ['Missing data for required field.']}}


def test_predict_unknown_model(client, app, regression, lin_reg):
    r = client.post('/api/predict',
        data=json.dumps({'features': {}, 'model': 'healthy-banana'}),
        content_type='application/json'
    )
    assert r.json == {'message': "No model named 'healthy-banana'."}


def test_predict(client, app, regression, lin_reg):
    r = client.post('/api/predict',
        data=json.dumps({'features': {}}),
        content_type='application/json'
    )
    assert r.status_code == 200
    assert 'prediction' in r.json


def test_predict_with_id(client, app, regression, lin_reg):

    r = client.post('/api/predict',
        data=json.dumps({'features': {}, 'id': '90210'}),
        content_type='application/json'
    )
    assert r.status_code == 201
    assert r.json == {'model': 'lin-reg', 'prediction': 0}

    with app.app_context():
        shelf = db.get_shelf()
        assert '#90210' in shelf


def test_learn_no_ground_truth(client, app, regression, lin_reg):
    r = client.post('/api/learn',
        data=json.dumps({'features': {'x': 1}}),
        content_type='application/json'
    )
    assert r.json == {'message': {'ground_truth': ['Missing data for required field.']}}


def test_learn_no_model(client, app, regression):
    r = client.post('/api/learn',
        data=json.dumps({'features': {'x': 1}, 'ground_truth': True}),
        content_type='application/json'
    )
    assert r.json == {'message': 'No default model has been set.'}


def test_learn_no_features(client, app, regression, lin_reg):
    r = client.post('/api/learn',
        data=json.dumps({'ground_truth': True}),
        content_type='application/json'
    )
    assert r.json == {'message': 'No features are stored and none were provided.'}


def test_learn(client, app, regression, lin_reg):
    r = client.post('/api/learn',
        data=json.dumps({'features': {'x': 1}, 'ground_truth': True}),
        content_type='application/json'
    )
    assert r.status_code == 201


def test_learn_with_id(client, app, regression, lin_reg):

    client.post('/api/predict',
        data=json.dumps({'id': 42, 'features': {'x': 1}}),
        content_type='application/json'
    )

    # Check the sample has been stored
    with app.app_context():
        shelf = db.get_shelf()
        assert sorted(shelf['#42'].keys()) == ['features', 'model', 'prediction']
        assert shelf['#42']['features'] == {'x': 1}

    r = client.post('/api/learn',
        data=json.dumps({'id': 42, 'ground_truth': True}),
        content_type='application/json'
    )
    assert r.status_code == 201

    # Check the sample has now been removed
    with app.app_context():
        shelf = db.get_shelf()
        assert '#42' not in shelf


def test_learn_unknown_id(client, app, regression, lin_reg):

    r = client.post('/api/learn',
        data=json.dumps({'id': 42, 'features': {'x': 1}, 'ground_truth': True}),
        content_type='application/json'
    )
    assert r.status_code == 400
    assert r.json == {'message': "No information stored for ID '42'."}
