from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from eggella import Eggella


from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

if TYPE_CHECKING:
    from anicli_api.base import BaseExtractor


class Config:
    EXTRACTOR: "BaseExtractor" = NotImplemented
    PLAYER: str = "mpv"
    PLAYER_EXTRA_ARGS: str = ""
    MIN_QUALITY: int = 0
    USE_FFMPEG_ROUTE: bool = False
    _CONFIG_PATH: str = "~/.config/ruanicli"


class AnicliApp(Eggella):
    CFG = Config()


app = AnicliApp("anicli", "~ ")
app.session = PromptSession("~ ", history=FileHistory(".anicli_history"), auto_suggest=AutoSuggestFromHistory())

app.documentation = """Anicli

This is a simple a TUI client for watching anime.
"""
