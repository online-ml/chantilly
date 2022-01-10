import pickle
import os
import uuid

from river import linear_model

from chantilly import cli
from chantilly import storage


def test_add_model(app):
    runner = app.test_cli_runner()

    # Pickle a model
    model = linear_model.LinearRegression()
    probe = uuid.uuid4()
    model.probe = probe
    with open('tmp.pkl', 'wb') as f:
        pickle.dump(model, f)

    # Add the model to the shelf through the CLI
    result = runner.invoke(cli.add_model, ['tmp.pkl', '--name', 'banana'])
    assert result.exit_code == 0

    # Check that the model has been added to the shelf
    with app.app_context():
        db = storage.get_db()
        assert isinstance(db['models/banana'], linear_model.LinearRegression)
        assert db['models/banana'].probe == probe

    # Delete the pickle
    os.remove('tmp.pkl')
