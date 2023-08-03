from anicli.cli import search
from anicli.cli import ongoing
from anicli.cli import events
from anicli.cli.config import app

APP = app
APP.register_blueprint(
    search.app,
    ongoing.app,
    events.app
)

