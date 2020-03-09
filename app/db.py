import os
import pickle
import shelve

import click
from creme import metrics
from flask import current_app, g
from flask.cli import with_appcontext
import influxdb


def get_influx() -> influxdb.InfluxDBClient:
    if 'influx' not in g:
        g.influx = influxdb.InfluxDBClient(
            host='localhost',
            port=8086,
            username='root',
            password='root',
            database=current_app.config['INFLUX_DB']
        )
    return g.influx


def close_influx(e=None):
    influx = g.pop('influx', None)

    if influx is not None:
        influx.close()


def init_influx():
    influx = get_influx()
    influx.create_database(current_app.config['INFLUX_DB'])


def get_shelf() -> shelve.Shelf:
    if 'shelf' not in g:
        g.shelf = shelve.open(current_app.config['SHELVE_PATH'])
    return g.shelf


def close_shelf(e=None):
    shelf = g.pop('shelf', None)

    if shelf is not None:
        shelf.close()


def init_db():

    if not current_app.config['API_ONLY']:
        influx = get_influx()
        influx.create_database(current_app.config['INFLUX_DB'])


def drop_db():

    os.remove(f"{current_app.config['SHELVE_PATH']}.db")

    if not current_app.config['API_ONLY']:
        influx = get_influx()
        influx.create_database(current_app.config['INFLUX_DB'])


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()


@click.command('add-model')
@click.argument('path')
@with_appcontext
def add_model_command(path):

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
    app.cli.add_command(add_model_command)
