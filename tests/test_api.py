import json
import pickle
import pytest
import uuid

import river
from river import datasets
from river import linear_model
from river import preprocessing
import flask

from chantilly import storage


@pytest.fixture
def regression(client):
    client.post('/api/init',
        data=json.dumps({'flavor': 'regression'}),
        content_type='application/json'
    )


@pytest.fixture
def lin_reg(client):
    model = preprocessing.StandardScaler() | linear_model.LinearRegression()
    client.post('/api/model/lin-reg', data=pickle.dumps(model))


def test_init_no_flavor(client, app):
    r = client.get('/api/init')
    assert r.status_code == 400
    assert r.json == {'message': 'No flavor has been set.'}


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
        assert storage.get_db()['flavor'].name == 'regression'

    assert client.get('/api/init').json == {
        'storage': app.config['STORAGE_BACKEND'],
        'flavor': 'regression',
        'river_version': river.__version__
    }


def test_model_no_flavor(client, app):
    model = linear_model.LinearRegression()
    r = client.post('/api/model', data=pickle.dumps(model))
    assert r.status_code == 400
    assert r.json == {'message': 'No flavor has been set.'}


class ModelWithoutFit:
    def predict_one(self, x):
        return True


def test_model_without_fit(client, app, regression):
    r = client.post('/api/model', data=pickle.dumps(ModelWithoutFit()))
    assert r.json == {'message': 'The model does not implement learn_one.'}


class ModelWithoutPredict:
    def learn_one(self, x, y):
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
        shelf = storage.get_db()
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


def test_delete_unknown_model(client, app, regression):
    assert client.delete('/api/model/kayser-soze').status_code == 404


def test_delete_model(client, app, regression):

    # Upload a model
    model = linear_model.LinearRegression()
    client.post('/api/model/healthy-banana', data=pickle.dumps(model))

    with app.app_context():
        assert 'models/healthy-banana' in storage.get_db()

    # Delete it
    client.delete('/api/model/healthy-banana')

    with app.app_context():
        assert 'models/healthy-banana' not in storage.get_db()


def test_models(client, app, regression):

    model = linear_model.LinearRegression()
    client.post('/api/model/ted-mosby', data=pickle.dumps(model))
    client.post('/api/model/barney-stinson', data=pickle.dumps(model))

    r = client.get('/api/models')
    assert r.json == {'default': 'barney-stinson', 'models': ['barney-stinson', 'ted-mosby']}


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
    assert r.json == {'message': {'features': ['required field']}}


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
        shelf = storage.get_db()
        assert '#90210' in shelf


def test_predict_model_name(client, app, regression, lin_reg):
    r = client.post('/api/predict',
        data=json.dumps({'features': {}, 'model': 'lin-reg'}),
        content_type='application/json'
    )
    assert r.status_code == 200
    assert r.json == {'model': 'lin-reg', 'prediction': 0.0}


def test_learn_no_ground_truth(client, app, regression, lin_reg):
    r = client.post('/api/learn',
        data=json.dumps({'features': {'x': 1}}),
        content_type='application/json'
    )
    assert r.json == {'message': {'ground_truth': ['required field']}}


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
        shelf = storage.get_db()
        assert sorted(shelf['#42'].keys()) == ['features', 'model', 'prediction']
        assert shelf['#42']['features'] == {'x': 1}

    r = client.post('/api/learn',
        data=json.dumps({'id': 42, 'ground_truth': True}),
        content_type='application/json'
    )
    assert r.status_code == 201

    # Check the sample has now been removed
    with app.app_context():
        shelf = storage.get_db()
        assert '#42' not in shelf


def test_learn_unknown_id(client, app, regression, lin_reg):

    r = client.post('/api/learn',
        data=json.dumps({'id': 42, 'features': {'x': 1}, 'ground_truth': True}),
        content_type='application/json'
    )
    assert r.status_code == 400
    assert r.json == {'message': "No information stored for ID '42'."}


def test_learn_model_name(client, app, regression, lin_reg):
    r = client.post('/api/learn',
        data=json.dumps({'features': {}, 'ground_truth': 7, 'model': 'lin-reg'}),
        content_type='application/json'
    )
    assert r.status_code == 201


def test_stats_no_flavor(client, app):
    r = client.get('/api/stats')
    assert r.status_code == 400
    assert r.json == {'message': 'No flavor has been set.'}


def test_stats(client, app, regression):
    r = client.get('/api/stats')
    assert r.status_code == 200
    assert r.json == {
        'learn': {
            'ewm_duration': 0,
            'ewm_duration_human': '0ns',
            'mean_duration': 0,
            'mean_duration_human': '0ns',
            'n_calls': 0
        },
        'predict': {
            'ewm_duration': 0,
            'ewm_duration_human': '0ns',
            'mean_duration': 0.0,
            'mean_duration_human': '0ns',
            'n_calls': 0
        }
    }


def test_stats_predict(client, app, regression, lin_reg):
    client.post('/api/predict', data=json.dumps({'features': {}}), content_type='application/json')
    stats = client.get('/api/stats').json
    assert stats['predict']['n_calls'] == 1
    assert stats['predict']['mean_duration'] > 0
    assert stats['predict']['ewm_duration'] > 0


def test_stats_learn(client, app, regression, lin_reg):
    client.post('/api/learn',
        data=json.dumps({'features': {}, 'ground_truth': True}),
        content_type='application/json'
    )
    stats = client.get('/api/stats').json
    assert stats['learn']['n_calls'] == 1
    assert stats['learn']['mean_duration'] > 0
    assert stats['learn']['ewm_duration'] > 0


def test_metrics_no_flavor(client, app):
    r = client.get('/api/metrics')
    assert r.json == {'message': 'No flavor has been set.'}


def test_metrics_with_flavor(client, app, regression):
    r = client.get('/api/metrics')
    assert len(r.json) > 0
