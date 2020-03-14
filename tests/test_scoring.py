import json
import math
import pickle

from creme import datasets
from creme import linear_model
from creme import metrics
from creme import preprocessing


def test_phishing(client, app):

    model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
    client.post('/api/model', data=pickle.dumps(model))

    for x, y in datasets.Phishing().take(30):

        # Predict/learn via chantilly
        r = client.post('/api/predict',
            data=json.dumps({'features': x}),
            content_type='application/json'
        )
        client.post('/api/learn',
            data=json.dumps({'features': x, 'target': y}),
            content_type='application/json'
        )

        # Predict/learn directly via creme
        y_pred = model.predict_proba_one(x)
        model.fit_one(x, y)

        # Compare the predictions from both sides
        assert math.isclose(y_pred[True], r.json['prediction']['true'])
