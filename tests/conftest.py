import os
import tempfile
import uuid

from creme import linear_model
from creme import metrics
from creme import preprocessing
import pytest

from chantilly import create_app
from chantilly import db


@pytest.fixture
def app():

    shelve_path = 'test'
    influx_name = str(uuid.uuid4())

    app = create_app({
        'TESTING': True,
        'INFLUX_DB': influx_name,
        'SHELVE_PATH': shelve_path
    })

    with app.app_context():
        db.init_influx()
        # Fixtures
        shelf = db.get_shelf()
        shelf['model'] = preprocessing.StandardScaler() | linear_model.LogisticRegression()
        shelf['metric'] = metrics.LogLoss()

    yield app

    os.remove(f'{shelve_path}.db')
    with app.app_context():
        db.get_influx().drop_database(influx_name)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
