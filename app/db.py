import os
import pickle
import shelve

import creme.base
import creme.metrics
import creme.utils
from flask import current_app, g
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


def set_model(model: creme.base.Estimator):
    shelf = get_shelf()
    shelf['model'] = model
    if isinstance(creme.utils.estimator_checks.guess_model(model), creme.base.Classifier):
        shelf['metrics'] = [creme.metrics.LogLoss()]
    else:
        shelf['metrics'] = [creme.metrics.MSE()]
