import logging

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from eggella import Eggella

from anicli_api.source import animego

from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments.styles import get_style_by_name

style = style_from_pygments_cls(get_style_by_name('monokai'))

logger = logging.getLogger("scrape_schema")
logger.setLevel(logging.DEBUG)
print(logger.handlers.pop(0))
logger.addHandler(
    logging.FileHandler("logs.log")
)

app = Eggella("anicli")
app.session = PromptSession("~ ", history=FileHistory(".anicli_history"), style=style)

EXTRACTOR = animego.Extractor()
PLAYER = "mpv"
# TODO add vlc and implement simple proxy server for redirects

PLAYER_ARGS = ""

# config path
# unix
# PATH = "~/.config/ruanicli"
# windows
# PATH = "%Appdata%/local/ruanicli"
