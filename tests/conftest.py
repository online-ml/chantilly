import os
import tempfile
import uuid

from creme import linear_model
from creme import metrics
from creme import preprocessing
import pytest

from app import create_app
from app import db


@pytest.fixture
def app():

    app = create_app({
        'TESTING': True,
        'INFLUX_DB': str(uuid.uuid4()),
        'SHELVE_PATH': str(uuid.uuid4()),
        'API_ONLY': True
    })

    with app.app_context():
        db.init_db()

        #
        shelf = db.get_shelf()
        shelf['model'] = preprocessing.StandardScaler() | linear_model.LogisticRegression()
        shelf['metric'] = metrics.LogLoss()

    yield app

    with app.app_context():
        db.drop_db()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
