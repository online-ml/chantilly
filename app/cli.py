import click
import dill
from flask.cli import with_appcontext

from . import db


@click.command('init-db')
@with_appcontext
def init_db_command():
    db.init_db()


@click.command('drop-db')
@with_appcontext
def drop_db_command():
    db.drop_db()


@click.command('set-model')
@click.argument('path')
@click.option('--reset_metrics', is_flag=True)
@with_appcontext
def set_model_command(path: str, reset_metrics: bool):

    with open(path, 'rb') as f:
        model = dill.load(f)
        db.set_model(model=model, reset_metrics=reset_metrics)

    click.echo('Model has been set.')
