from anicli2.legacy.cli import search, ongoing, events
from anicli import AnicliApp

APP = AnicliApp("anicli-main")
APP.register_blueprint(search.app, ongoing.app, events.app)
