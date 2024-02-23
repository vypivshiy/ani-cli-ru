from anicli.cli import events, ongoing, search
from anicli.cli.config import AnicliApp

APP = AnicliApp("anicli-main")
APP.register_blueprint(search.app, ongoing.app, events.app)
