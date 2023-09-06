import sys
from typing import TYPE_CHECKING, Optional
from pathlib import Path

from eggella import Eggella
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts.prompt import CompleteStyle
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from anicli.cli.compat import tomllib

if TYPE_CHECKING:
    from anicli_api.base import BaseExtractor

_DEFAULT_APP_CONFIG = {
    "source": "animego",
    "minimal_quality": 0,
    "player": "mpv",
    "ffmpeg_proxy": False,
    "proxy": "",
    "timeout": "",
    # ADVANCED player keys config
    "player_arguments": {
        "cmd_title": '--title="{}"',
        "cmd_headers_arg": '--http-header-fields="{}: {}"',
        "cmd_extra_args": ""
    }
}


def _is_exists_config():
    path = get_path_config()
    file = path / "config.toml"
    return file.exists()


def _create_new_config():
    """create default file config if not exists()"""
    if not _is_exists_config():
        with open(get_path_config() / "config.toml", "w") as f:
            f.write(tomllib.dumps(_DEFAULT_APP_CONFIG))


def get_file_config() -> Path:
    if not _is_exists_config():
        _create_new_config()
    return get_path_config() / "config.toml"


def get_path_config() -> Path:
    if sys.platform == "win32":
        path = Path.home() / "AppData" / "Roaming" / "anicliru"
        path.mkdir(exist_ok=True, parents=True)
        return path

    path = Path.home() / ".config" / "anicliru"
    path.mkdir(exist_ok=True, parents=True)
    return path


class Config:
    EXTRACTOR: "BaseExtractor" = NotImplemented
    PLAYER: str = "mpv"
    MIN_QUALITY: int = 0
    USE_FFMPEG_ROUTE: bool = False
    CONFIG_PATH: str = str(get_file_config())

    PROXY: Optional[str] = None
    TIMEOUT: Optional[float] = None

    PLAYER_ARGS: dict[str, str] = {}

    @classmethod
    def httpx_kwargs(cls):
        return {"proxies": cls.PROXY, "timeout": cls.TIMEOUT}


# app configuration
class AnicliApp(Eggella):
    CFG = Config()


app = AnicliApp("anicli", "~ ")
app.session = PromptSession("~ ",
                            history=FileHistory(str(get_path_config() / ".anicli_history")),
                            auto_suggest=AutoSuggestFromHistory(),
                            complete_style=CompleteStyle.MULTI_COLUMN)

app.documentation = """Anicli

This is a simple a TUI client for watching anime.
"""
