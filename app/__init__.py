import os

import click
import dill
import flask
import flask.cli
import shelve

from . import db
from . import cli
from . import exceptions


# Make the shelve module use dill as a backend instead of the default which is pickle
shelve.Pickler = dill.Pickler  # type: ignore
shelve.Unpickler = dill.Unpickler  # type: ignore


def create_app(test_config: dict = None):

    app = flask.Flask('chantilly', instance_relative_config=True)

    # Set default configuation
    app.config.from_mapping(
        SECRET_KEY='dev',
        SHELVE_PATH='chantilly'
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

    app.teardown_appcontext(db.close_shelf)
    app.cli.add_command(cli.init)
    app.cli.add_command(cli.add_model)
    app.cli.add_command(cli.delete_model)

    from . import api
    app.register_blueprint(api.bp)

    from . import dashboard
    app.register_blueprint(dashboard.bp)
    app.add_url_rule('/', endpoint='index')

    # Register exception handler
    @app.errorhandler(exceptions.InvalidUsage)
    def handle_invalid_usage(error):
        response = flask.jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    # https://flask.palletsprojects.com/en/1.1.x/patterns/favicon/
    @app.route('/favicon.ico')
    def favicon():
        return flask.send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon'
        )

    return app


@click.group(cls=flask.cli.FlaskGroup, create_app=create_app)
def cli_hook():
    """Management script for the chantilly application."""
