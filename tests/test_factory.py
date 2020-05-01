from chantilly import create_app


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_index(client):
    r = client.get('/')
    assert r.status_code == 200
