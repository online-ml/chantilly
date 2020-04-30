import uuid
import pytest

from app import create_app
from app import storage


def pytest_addoption(parser):
    parser.addoption('--redis', action='store_true', help='run with redis')


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
            'REDIS_HOST': 'localhost'
        }

    app = create_app(config)

    # app.create_app({
    #     'SECRET_KEY': 'dev',
    #     'STORAGE_BACKEND': 'redis',
    #     'REDIS_HOST': 'localhost'
    # })

    yield app

    with app.app_context():
        storage.drop_db()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
