import pickle

import click
from flask.cli import with_appcontext

from . import db


@click.command('init-db')
@with_appcontext
def init_db_command():
    db.init_db()


@click.command('set-model')
@click.argument('path')
@with_appcontext
def set_model_command(path):

    with open(path, 'rb') as f:
        model = pickle.load(f)
        db.set_model(model)

    click.echo('Model has been set.')
