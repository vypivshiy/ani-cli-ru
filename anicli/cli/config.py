import logging

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from eggella import Eggella

from anicli_api.source import animego

from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

logger = logging.getLogger("scrape_schema")
logger.setLevel(logging.DEBUG)
print(logger.handlers.pop(0))
logger.addHandler(
    logging.FileHandler("logs.log")
)

app = Eggella("anicli", "~ ")
app.session = PromptSession("~ ", history=FileHistory(".anicli_history"), auto_suggest=AutoSuggestFromHistory())
app.documentation = """Anicli

This is a TUI client for watching anime.
"""
EXTRACTOR = animego.Extractor()
PLAYER = "mpv"
# TODO add vlc and implement simple proxy server for redirects

PLAYER_ARGS = ""

# config path
# unix
# PATH = "~/.config/ruanicli"
# windows
# PATH = "%Appdata%/local/ruanicli"
