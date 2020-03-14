import pytest

from app import db


def test_write_read(app):

    if app.config['API_ONLY']:
        pytest.skip('Running in API only mode')

    with app.app_context():
        influx = db.get_influx()

        assert len(influx.query('SELECT cakes FROM sales;')) == 0

        ok = influx.write_points([{
            'measurement': 'sales',
            'fields': {
                'cakes': 42
            }
        }])
        assert ok

        assert len(influx.query('SELECT cakes FROM sales;')) == 1


