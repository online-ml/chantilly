import os

import click
from flask import Flask
from flask.cli import FlaskGroup

from . import db
from . import cli


def create_app(test_config=None):

    app = Flask('chantilly', instance_relative_config=True)

    # Set default configuation
    app.config.from_mapping(
        SECRET_KEY='dev',
        INFLUX_DB='chantilly',
        SHELVE_PATH='chantilly',
        API_ONLY=False
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # A simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    app.teardown_appcontext(db.close_influx)
    app.teardown_appcontext(db.close_shelf)
    app.cli.add_command(cli.init_db_command)
    app.cli.add_command(cli.set_model_command)

    # Register routes
    from . import api
    app.register_blueprint(api.bp)

    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli_hook():
    """Management script for the chantilly application."""
