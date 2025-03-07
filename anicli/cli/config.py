from pathlib import Path
from typing import TYPE_CHECKING, Optional

from eggella import Eggella
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts.prompt import CompleteStyle

# import tomli


if TYPE_CHECKING:
    from anicli_api.base import BaseExtractor


class Config:
    EXTRACTOR: "BaseExtractor" = NotImplemented
    PLAYER: str = "mpv"
    PLAYER_EXTRA_ARGS: str = ""
    MIN_QUALITY: int = 1080
    USE_FFMPEG_ROUTE: bool = False
    # TODO add config file
    _CONFIG_PATH: str = "~/.config/ruanicli"
    _CONFIG_NAME: str = "config.toml"
    _DB_NAME: str = "anicli.db"

    # httpx params
    PROXY: Optional[str] = None
    TIMEOUT: Optional[float] = None
    # m3u for SLICE play mode
    M3U_MAKE: bool = True
    M3U_MAX_SIZE: int = 12

    @classmethod
    def httpx_kwargs(cls):
        return {"proxy": cls.PROXY, "timeout": cls.TIMEOUT}

    @classmethod
    def exists_config(cls) -> bool:
        cfg_path = Path(cls._CONFIG_PATH) / cls._CONFIG_NAME
        return Path(cls._CONFIG_PATH).exists() and cfg_path.exists()


class AnicliApp(Eggella):
    CFG = Config()

    def exec_and_loop(self, key: str, args: str):

        self.cmd.print_ft(self.intro)
        self._load_blueprints()
        self._command_manager.register_buildin_commands()
        self._handle_startup_events()

        # run command and handle loop
        self.command_manager.exec(key, args)

        self._handle_commands()
        self._handle_close_events()


app = AnicliApp("anicli", "~ ")
app.session = PromptSession(
    "~ ",
    history=FileHistory(".anicli_history"),
    auto_suggest=AutoSuggestFromHistory(),
    complete_style=CompleteStyle.MULTI_COLUMN,
)

app.documentation = """Anicli

This is a simple a TUI client for watching anime.
"""
