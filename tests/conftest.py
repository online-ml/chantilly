import uuid

from chantilly import create_app
from chantilly import storage
import pytest


def pytest_addoption(parser):
    parser.addoption('--redis', action='store_true', help='redis storage backend')


def pytest_generate_tests(metafunc):

    backends = ['shelve']

    if metafunc.config.getoption('redis'):
        backends.append('redis')

    if 'app' in metafunc.fixturenames:
        metafunc.parametrize('app', backends, indirect=True)


@pytest.fixture
def app(request):

    if request.param == 'shelve':
        config = {
            'TESTING': True,
            'SHELVE_PATH': str(uuid.uuid4())
        }
    elif request.param == 'redis':
        config = {
            'SECRET_KEY': 'dev',
            'STORAGE_BACKEND': 'redis',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': 6379,
            'REDIS_DB': 0
        }

    app = create_app(config)

    yield app

    with app.app_context():
        storage.drop_db()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
