import flask


bp = flask.Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    return flask.render_template('index.html')
