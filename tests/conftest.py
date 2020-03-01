import os
import tempfile

from creme import linear_model
from creme import metrics
from creme import preprocessing
import pytest

from chantilly import create_app
from chantilly import db


@pytest.fixture
def app():

    shelve_path = 'test'

    app = create_app({
        'TESTING': True,
        'SHELVE_PATH': shelve_path
    })

    with app.app_context():
        db.init_influx()
        shelf = db.get_shelf()
        shelf['model'] = preprocessing.StandardScaler() | linear_model.LogisticRegression()
        shelf['metric'] = metrics.LogLoss()

    yield app

    os.remove(f'{shelve_path}.db')


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
