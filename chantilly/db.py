import pickle
import shelve

import click
from creme import metrics
from flask import current_app, g
from flask.cli import with_appcontext
import influxdb


def get_influx():
    if 'influx' not in g:
        g.influx = influxdb.InfluxDBClient(
            'localhost', 8086, 'root', 'root', 'example'
        )
    return g.influx


def close_influx(e=None):
    influx = g.pop('influx', None)

    if influx is not None:
        influx.close()


def init_influx():
    influx = get_influx()
    influx.create_database('example')


def get_shelf():
    if 'shelf' not in g:
        g.shelf = shelve.open(current_app.config['SHELVE_PATH'])
    return g.shelf


def close_shelf(e=None):
    shelf = g.pop('shelf', None)

    if shelf is not None:
        shelf.close()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_influx()
    click.echo('Initialized the InfluxDB instance.')


@click.command('init-model')
@click.argument('path')
@with_appcontext
def init_model_command(path):

    shelf = get_shelf()
    with open(path, 'rb') as f:
        model = pickle.load(f)
        shelf['model'] = model
        shelf['metric'] = metrics.LogLoss()

    click.echo('Added the model to the shelf.')


def init_app(app):
    app.teardown_appcontext(close_influx)
    app.teardown_appcontext(close_shelf)
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_model_command)
