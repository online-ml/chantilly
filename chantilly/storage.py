import abc
import contextlib
import os
import random
import shelve

import river.base
import river.metrics
import river.stats
import river.utils
import dill
import flask
try:
    import redis
except ImportError:
    pass

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

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class ShelveBackend(shelve.DbfilenameShelf, StorageBackend):  # type: ignore
    """Storage backend based on the shelve module from the standard library.

    This should mainly be used for development and testing, but not production.

    """


class RedisBackend(StorageBackend):

    def __init__(self, host, port, db):
        self.r = redis.Redis(host=host, port=port, db=db)

    def __setitem__(self, key, obj):
        self.r[key] = dill.dumps(obj)

    def __getitem__(self, key):
        return dill.loads(self.r[key])

    def __delitem__(self, key):
        self.r.delete(key)

    def __iter__(self):
        for key in self.r.scan_iter():
            yield key.decode()

    def close(self):
        return


# The following will make it so that shelve.open returns ShelveBackend instead of DbfilenameShelf
shelve.DbfilenameShelf = ShelveBackend  # type: ignore


def get_db() -> StorageBackend:
    if 'db' not in flask.g:

        backend = flask.current_app.config['STORAGE_BACKEND']

        if backend == 'shelve':
            flask.g.db = shelve.open(flask.current_app.config['SHELVE_PATH'])

        elif backend == 'redis':
            flask.g.db = RedisBackend(
                host=flask.current_app.config['REDIS_HOST'],
                port=int(flask.current_app.config['REDIS_PORT']),
                db=int(flask.current_app.config['REDIS_DB'])
            )

        else:
            raise ValueError(f'Unknown storage backend: {backend}')

    return flask.g.db


def close_db(e=None):
    db = flask.g.pop('db', None)

    if db is not None:
        db.close()


def drop_db():
    """This function's responsability is to wipe out a database.

    This could be implement within each StorageBackend, it's just a bit more akward because at this
    point the database connection is not stored in the app anymore.

    """

    backend = flask.current_app.config['STORAGE_BACKEND']

    if backend == 'shelve':
        path = flask.current_app.config['SHELVE_PATH']
        with contextlib.suppress(FileNotFoundError):
            os.remove(f'{path}.db')

    elif backend == 'redis':
        r = redis.Redis(
            host=flask.current_app.config['REDIS_HOST'],
            port=flask.current_app.config.get('REDIS_PORT', 6379),
            db=flask.current_app.config.get('REDIS_DB', 0)
        )
        r.flushdb()


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
        'learn_mean': river.stats.Mean(),
        'learn_ewm': river.stats.EWMean(.3),
        'predict_mean': river.stats.Mean(),
        'predict_ewm': river.stats.EWMean(.3),
    }

def init_metrics():

    db = get_db()
    try:
        flavor = db['flavor']
    except KeyError:
        raise exceptions.FlavorNotSet

    db['metrics'] = flavor.default_metrics()


def add_model(model: river.base.Estimator, name: str = None) -> str:

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
