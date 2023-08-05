from anicli.cli import APP
import importlib
__version__ = "5.0.3"


def run_cli():
    import argparse
    parser = argparse.ArgumentParser(description="anicli-ru")
    parser.add_argument("-s", "--source", default="animego", choices=["animego", "sovetromantica",
                                                                      "animejoy",
                                                                      "anilibria",
                                                                      "animevost"],
                        help="Anime source provider. DEFAULT `animego`")
    parser.add_argument("-q", "--quality",
                        type=int,
                        default=0,
                        choices=[0, 144, 240, 360, 480, 720, 1080],
                        help="Set minimal video quality output. "
                             "If there is no maximum, it will display the closest value"
                        )
    parser.add_argument("-p", "--player",
                        type=str,
                        default="mpv",
                        choices=["mpv", "vlc", "cvlc"],
                        help="Set videoplayer target. Default mpv"
                        )

    parser.add_argument("--ffmpeg",
                        action="store_true",
                        default=False,
                        help="usage ffmpeg backend for redirect video to player. "
                             "Enable, if your player cannot accept headers params"
                        )
    parser.add_argument("--proxy",
                        type=str,
                        default=None,
                        help="Setup proxy")
    parser.add_argument("--timeout",
                        type=float,
                        default=None,
                        help="Setup timeout")

    namespaces = parser.parse_args()
    module = importlib.import_module(f"anicli_api.source.{namespaces.source}")
    APP.CFG.EXTRACTOR = getattr(module, "Extractor")()
    APP.CFG.USE_FFMPEG_ROUTE = namespaces.ffmpeg
    APP.CFG.PLAYER = namespaces.player
    APP.CFG.MIN_QUALITY = namespaces.quality
    APP.CFG.TIMEOUT = namespaces.timeout
    APP.CFG.PROXY = namespaces.proxy
    APP.loop()


if __name__ == '__main__':
    run_cli()
