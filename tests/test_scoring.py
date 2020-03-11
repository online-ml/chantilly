import json
import math

from creme import datasets
from creme import linear_model
from creme import metrics
from creme import preprocessing
import pytest


@pytest.mark.skip(reason='no way of currently testing this')
def test_phishing(client, app):

    m1 = metrics.LogLoss()
    m2 = metrics.LogLoss()

    model = preprocessing.StandardScaler() | linear_model.LogisticRegression()

    for x, y in datasets.Phishing().take(10):

        # Predict/learn via chantilly
        r = client.post('/api/predict',
            data=json.dumps({'features': x}),
            content_type='application/json'
        )
        m1.update(y_true=y, y_pred=r.json['prediction'])
        client.post('/api/learn',
            data=json.dumps({'features': x, 'target': y}),
            content_type='application/json'
        )

        # Predict/learn directly via creme
        y_pred = model.predict_proba_one(x)
        m2.update(y_true=y, y_pred=y_pred)
        model.fit_one(x, y)

    assert math.isclose(m1.get(), m2.get())
