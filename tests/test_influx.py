from chantilly import db

def test_write_read(app):

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


