from typing import TYPE_CHECKING, Optional
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts.prompt import CompleteStyle
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
    CONFIG_PATH: str = Path.home() / ".config" / "ruanicli"

    PROXY: Optional[str] = None
    TIMEOUT: Optional[float] = None

    @classmethod
    def httpx_kwargs(cls):
        return {"proxies": cls.PROXY, "timeout": cls.TIMEOUT}


class AnicliApp(Eggella):
    CFG = Config()


app = AnicliApp("anicli", "~ ")
app.session = PromptSession("~ ", history=FileHistory(".anicli_history"), auto_suggest=AutoSuggestFromHistory(),
                            complete_style=CompleteStyle.MULTI_COLUMN)

app.documentation = """Anicli

This is a simple a TUI client for watching anime.
"""
