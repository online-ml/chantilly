import contextlib
import os
import shelve

import creme.base
import creme.metrics
import creme.utils
from flask import current_app, g


def get_shelf() -> shelve.Shelf:
    if 'shelf' not in g:
        g.shelf = shelve.open(current_app.config['SHELVE_PATH'])
    return g.shelf


def close_shelf(e=None):
    shelf = g.pop('shelf', None)

    if shelf is not None:
        shelf.close()


def init_db():
    pass


def drop_db():

    with contextlib.suppress(FileNotFoundError):
        os.remove(f"{current_app.config['SHELVE_PATH']}.db")


def set_model(model: creme.base.Estimator, reset_metrics: bool):
    shelf = get_shelf()
    shelf['model'] = model

    if not reset_metrics and 'metrics' in shelf:
        return

    if isinstance(creme.utils.estimator_checks.guess_model(model), creme.base.Classifier):
        shelf['metrics'] = [creme.metrics.LogLoss()]
    else:
        shelf['metrics'] = [creme.metrics.MSE()]
