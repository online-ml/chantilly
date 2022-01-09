import json
import math
import pickle

from river import datasets
from river import feature_extraction
from river import linear_model
from river import naive_bayes
from river import preprocessing


def test_phishing(client, app):

    r = client.post('/api/init', json={'flavor': 'binary'})

    model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
    client.post('/api/model', data=pickle.dumps(model))

    for i, (x, y) in enumerate(datasets.Phishing().take(30)):

        # Predict/learn via chantilly
        r = client.post('/api/predict',
            data=json.dumps({'id': i, 'features': x}),
            content_type='application/json'
        )

        client.post('/api/learn',
            data=json.dumps({'id': i, 'ground_truth': y}),
            content_type='application/json'
        )

        # Predict/learn directly via river
        y_pred = model.predict_proba_one(x)
        model.learn_one(x, y)

        # Compare the predictions from both sides
        assert math.isclose(y_pred[True], r.json['prediction']['true'])


def test_phishing_without_id(client, app):

    r = client.post('/api/init', json={'flavor': 'binary'})

    model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
    client.post('/api/model', data=pickle.dumps(model))

    for x, y in datasets.Phishing().take(30):

        # Predict/learn via chantilly
        r = client.post('/api/predict',
            data=json.dumps({'features': x}),
            content_type='application/json'
        )
        client.post('/api/learn',
            data=json.dumps({'features': x, 'ground_truth': y}),
            content_type='application/json'
        )

        # Predict/learn directly via river
        y_pred = model.predict_proba_one(x)

        # Because no ID is provided, chantilly will ask the model to make a prediction a second
        # time in order to update the metric
        model.predict_proba_one(x)

        model.learn_one(x, y)

        # Compare the predictions from both sides
        assert math.isclose(y_pred[True], r.json['prediction']['true'])


def test_text_input(client, app):

    client.post('/api/init', json={'flavor': 'binary'})

    model = feature_extraction.BagOfWords() | naive_bayes.MultinomialNB()
    client.post('/api/model', data=pickle.dumps(model))

    for x, y in datasets.SMSSpam().take(20):

        # Predict/learn via chantilly
        p = client.post('/api/predict',
            data=json.dumps({'features': x['body']}),
            content_type='application/json'
        )
        print(p.json)
        assert p.status_code == 200
        l = client.post('/api/learn',
            data=json.dumps({'features': x['body'], 'ground_truth': y}),
            content_type='application/json'
        )
        assert l.status_code == 201

         # Predict/learn directly via river
        y_pred = model.predict_proba_one(x['body'])
        model.learn_one(x['body'], y)

        # Compare the predictions from both sides
        assert y_pred.get(True) == p.json['prediction'].get('true')
        assert y_pred.get(False) == p.json['prediction'].get('false')
