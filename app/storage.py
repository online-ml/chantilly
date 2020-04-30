import abc
import contextlib
import os
import random
import shelve

import creme.base
import creme.metrics
import creme.stats
import creme.utils
import flask

from . import exceptions
from . import flavors


class StorageBackend(abc.ABC):
    """Abstract storage backend.

    This interface defines a set of methods to implement in order for a database to be used as a
    storage backend. This allows using different databases in a homogeneous manner by proving a
    single interface.

    """

    @abc.abstractmethod
    def __setitem__(self, key, obj):
        """Store an object."""

    @abc.abstractmethod
    def __getitem__(self, key):
        """Retrieve an object."""

    @abc.abstractmethod
    def __delitem__(self, key):
        """Remove an object from storage."""

    @abc.abstractmethod
    def __iter__(self):
        """Iterate over the keys."""

    @abc.abstractmethod
    def close(self):
        """Do something when the app shuts down."""

    @abc.abstractmethod
    def __del__(self):
        """Delete everything."""

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


# class ShelveBackend(StorageBackend):
#     """Storage backend based on the shelve module from the standard library.

#     This should mainly be used for development and testing, but not production.

#     """

#     def __init__(self, path):
#         self.path = path
#         self.shelf = shelve.open(path)

#     def __setitem__(self, key, obj):
#         self.shelf[key] = obj

#     def __getitem__(self, key):
#         return self.shelf[key]

#     def __delitem__(self, key):
#         del self.shelf[key]

#     def __iter__(self):
#         return iter(self.shelf)

#     def close(self):
#         self.shelf.close()

#     def __del__(self):
#         with contextlib.suppress(FileNotFoundError):
#             os.remove(f'{self.path}.db')


def get_db() -> StorageBackend:
    if 'db' not in flask.g:

        backend = flask.current_app.config['STORAGE_BACKEND']

        if backend == 'shelve':
            flask.g.db = shelve.open(flask.current_app.config['SHELVE_PATH'])
        else:
            raise ValueError(f'Unknown storage backend: {backend}')

    return flask.g.db


def close_db(e=None):
    db = flask.g.pop('db', None)

    if db is not None:
        db.close()


def drop_db():
    """This function's responsability is to wipe out a database."""

    backend = flask.current_app.config['STORAGE_BACKEND']

    if backend == 'shelve':
        path = flask.current_app.config['SHELVE_PATH']
        with contextlib.suppress(FileNotFoundError):
            os.remove(f'{path}.db')


def set_flavor(flavor: str):

    drop_db()

    try:
        flavor = flavors.allowed_flavors()[flavor]
    except KeyError:
        raise exceptions.UnknownFlavor

    db = get_db()
    db['flavor'] = flavor

    init_metrics()
    init_stats()


def init_stats():
    db = get_db()
    db['stats'] = {
        'learn_mean': creme.stats.Mean(),
        'learn_ewm': creme.stats.EWMean(.3),
        'predict_mean': creme.stats.Mean(),
        'predict_ewm': creme.stats.EWMean(.3),
    }

def init_metrics():

    db = get_db()
    try:
        flavor = db['flavor']
    except KeyError:
        raise exceptions.FlavorNotSet

    db['metrics'] = flavor.default_metrics()


def add_model(model: creme.base.Estimator, name: str = None) -> str:

    db = get_db()

    # Pick a name if none is given
    if name is None:
        while True:
            name = _random_slug()
            if f'models/{name}' not in db:
                break

    db[f'models/{name}'] = model

    return name


def delete_model(name: str):
    db = get_db()
    del db['models/{name}']


def _random_slug(rng=random) -> str:
    """

    >>> rng = random.Random(42)
    >>> _random_slug(rng)
    'earsplitting-apricot'

    """
    here = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(here, 'adjectives.txt')) as f, open(os.path.join(here, 'food_names.txt')) as g:
        return f'{rng.choice(f.read().splitlines())}-{rng.choice(g.read().splitlines())}'
