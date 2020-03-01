import json

from chantilly import db


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
        shelf = db.get_shelf()
        metric = shelf['metric']
        assert metric.n == 1


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
        shelf = db.get_shelf()
        metric = shelf['metric']
        assert metric.n == 1
