import pickle
import os

from creme import linear_model
from flask import g

from app import db


def test_set_model(app):
    runner = app.test_cli_runner()

    # Pickle a model
    model = linear_model.LinearRegression()
    model.id = 'hey_im_an_id'
    with open('tmp.pkl', 'wb') as f:
        pickle.dump(model, f)

    # Add the model to the shelf through the CLI
    result = runner.invoke(db.set_model_command, ['tmp.pkl'])
    assert result.exit_code == 0

    # Check that the model has been added to the shelf
    with app.app_context():
        shelf = db.get_shelf()
        assert isinstance(shelf['model'], linear_model.LinearRegression)
        assert shelf['model'].id == 'hey_im_an_id'

    # Delete the pickle
    os.remove('tmp.pkl')
