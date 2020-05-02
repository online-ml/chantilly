from creme import datasets
from creme import linear_model
from creme import preprocessing
import dill
import requests


if __name__ == '__main__':

    host = 'http://localhost:5000'

    # Set a flavor
    r = requests.post(host + '/api/init', json={'flavor': 'regression'})
    assert r.status_code == 201

    # Upload a model
    model = preprocessing.StandardScaler() | linear_model.LinearRegression()
    r = requests.post(host + '/api/model', data=dill.dumps(model))
    assert r.status_code == 201

    # Train on some data
    for x, y in datasets.TrumpApproval().take(30):
        r = requests.post(host + '/api/learn', json={
            'features': x,
            'ground_truth': y
        })
        assert r.status_code == 201
