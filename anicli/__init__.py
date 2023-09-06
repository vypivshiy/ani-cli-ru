import argparse
import importlib
from typing import Any, Dict

from anicli.cli import APP
from anicli.cli.config import get_file_config
from anicli.cli.compat import tomllib
from anicli.cli_utlis import is_ffmpeg_installed, is_player_installed

__version__ = "5.0.3"


def _read_file_config() -> Dict[str, Any]:
    with open(get_file_config(), "r") as f:
        cfg = tomllib.load(f)
    return cfg


def _run_app(namespaces: argparse.Namespace):
    """parse config and run application"""
    cfg = _read_file_config()
    module_name = namespaces.source or cfg['source']
    module = importlib.import_module(f"anicli_api.source.{module_name}")
    APP.CFG.EXTRACTOR = getattr(module, "Extractor")()
    APP.CFG.USE_FFMPEG_ROUTE = namespaces.ffmpeg or cfg["ffmpeg_proxy"]
    APP.CFG.PLAYER = namespaces.player or cfg["player"]
    APP.CFG.PLAYER_ARGS = cfg["player_arguments"]

    if not is_player_installed(APP.CFG.PLAYER):
        print(f"Error! Player {APP.CFG.PLAYER} not found")
        exit(1)

    APP.CFG.MIN_QUALITY = namespaces.quality or cfg['minimal_quality']
    APP.CFG.TIMEOUT = namespaces.timeout or cfg['timeout']
    APP.CFG.PROXY = namespaces.proxy or cfg["proxy"]
    APP.loop()


def run_cli():
    import argparse
    parser = argparse.ArgumentParser(description="anicli-ru")
    parser.add_argument("-s", "--source", choices=["animego", "sovetromantica",
                                                                      "animejoy",
                                                                      "anilibria",
                                                                      "animevost"],
                        help="Anime source provider. DEFAULT `animego`")
    parser.add_argument("-q", "--quality",
                        type=int,
                        choices=[0, 144, 240, 360, 480, 720, 1080],
                        help="Set minimal video quality output. "
                             "If there is no maximum, it will display the closest value"
                        )
    parser.add_argument("-p", "--player",
                        type=str,
                        choices=["mpv", "vlc", "cvlc"],
                        help="Set videoplayer target. Default mpv"
                        )

    parser.add_argument("--ffmpeg",
                        action="store_true",
                        help="usage ffmpeg proxy for redirect video to player. "
                             "Enable, if your player cannot accept headers params or stream video"
                             "from the internet"
                        )
    parser.add_argument("--proxy",
                        type=str,
                        help="Setup proxy")
    parser.add_argument("--timeout",
                        type=float,
                        help="Setup timeout")

    parser.add_argument("--version",
                        action="store_true",
                        default=False,
                        help="Show app version")

    namespaces = parser.parse_args()
    if namespaces.version:
        print("anicli-ru", __version__)
        exit(0)
    if namespaces.ffmpeg and not is_ffmpeg_installed():
        print("ffmpeg not found, please, install ffmpeg")
        exit(1)

    _run_app(namespaces)


if __name__ == '__main__':
    run_cli()
