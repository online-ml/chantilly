import contextlib
import os
import shelve
import typing

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

    model = creme.utils.estimator_checks.guess_model(model)

    if isinstance(model, creme.base.BinaryClassifier):
        shelf['metrics'] = [
            creme.metrics.Accuracy(),
            creme.metrics.LogLoss(),
            creme.metrics.Precision(),
            creme.metrics.Recall(),
            creme.metrics.F1()
        ]
    elif isinstance(model, creme.base.MultiClassifier):
        shelf['metrics'] = [
            creme.metrics.Accuracy(),
            creme.metrics.CrossEntropy(),
            creme.metrics.MacroPrecision(),
            creme.metrics.MacroRecall(),
            creme.metrics.MacroF1(),
            creme.metrics.MicroPrecision(),
            creme.metrics.MicroRecall(),
            creme.metrics.MicroF1()
        ]
    elif isinstance(model, creme.base.Regressor):
        shelf['metrics'] = [
            creme.metrics.MAE(),
            creme.metrics.RMSE(),
            creme.metrics.SMAPE()
        ]
    else:
        raise ValueError('Unknown model type')
