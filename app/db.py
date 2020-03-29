import contextlib
import os
import random
import shelve

import creme.base
import creme.metrics
import creme.utils
import flask

from . import exceptions
from . import flavors


def get_shelf() -> shelve.Shelf:
    if 'shelf' not in flask.g:
        flask.g.shelf = shelve.open(flask.current_app.config['SHELVE_PATH'])
    return flask.g.shelf


def close_shelf(e=None):
    shelf = flask.g.pop('shelf', None)

    if shelf is not None:
        shelf.close()


def drop_db():

    # Delete the current shelf if it exists
    with contextlib.suppress(FileNotFoundError):
        os.remove(f"{flask.current_app.config['SHELVE_PATH']}.db")


def set_flavor(flavor: str):

    drop_db()

    try:
        flavor = flavors.allowed_flavors()[flavor]
    except KeyError:
        raise exceptions.UnknownFlavor

    shelf = get_shelf()
    shelf['flavor'] = flavor

    reset_metrics()


def reset_metrics():

    shelf = get_shelf()
    try:
        flavor = shelf['flavor']
    except KeyError:
        raise exceptions.FlavorNotSet

    shelf['metrics'] = flavor.default_metrics()


def add_model(model: creme.base.Estimator, name: str = None) -> str:

    shelf = get_shelf()

    # Pick a name if none is given
    if name is None:
        while True:
            name = _random_slug()
            if f'models/{name}' not in shelf:
                break

    shelf[f'models/{name}'] = model

    return name


def delete_model(name: str):
    shelf = get_shelf()
    del shelf['models/{name}']


def _random_slug(rng=random) -> str:
    """

    >>> rng = random.Random(42)
    >>> _random_slug(rng)
    'earsplitting-apricot'

    """
    here = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(here, 'adjectives.txt')) as f, open(os.path.join(here, 'food_names.txt')) as g:
        return f'{rng.choice(f.read().splitlines())}-{rng.choice(g.read().splitlines())}'
