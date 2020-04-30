import uuid
import pytest

from app import create_app
from app import storage


@pytest.fixture
def app():

    app = create_app({
        'TESTING': True,
        'SHELVE_PATH': str(uuid.uuid4())
    })

    yield app

    with app.app_context():
        storage.drop_db()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
