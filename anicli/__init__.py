import warnings

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated as A, Optional
else:
    from typing_extensions import Annotated as A

from typing import TYPE_CHECKING

import typer
from typer import Option as Opt

from .tui import AnicliRuTui
from .utils.fetch_extractors import get_extractor_modules

if TYPE_CHECKING:
    from .types_ import TYPER_CONTEXT_OPTIONS

APP = typer.Typer()
SOURCE_CHOICES = get_extractor_modules()
QUALITY_CHOICES = [0, 360, 480, 720, 1080]


def _validate_source(source: str) -> str:
    if source not in SOURCE_CHOICES:
        msg = f'value {source} not in {SOURCE_CHOICES}'
        raise typer.BadParameter(msg)
    return source


def _validate_quality(quality: int) -> int:
    if quality not in QUALITY_CHOICES:
        msg = f'value {quality} not in {QUALITY_CHOICES}'
        raise typer.BadParameter(msg)
    return quality


def _mpv_args_convert(mpv_args: str):
    if not mpv_args:
        return {}
    new_mpv_args = mpv_args.split(' ')


@APP.callback()
def main(
        ctx: typer.Context,
        source: str = Opt(
            'animego',
            "-s", '--source',
            help=f'source extractor. default "animego". Available sources: {SOURCE_CHOICES}',
            callback=_validate_source
        ),
        quality: int = Opt(0,
                           '-q', '--quality',
                           help=f'set prefered video quality. if value == 0 - add manual choice in app. '
                                f'Available qualities: {QUALITY_CHOICES}',
                           callback=_validate_quality),
        proxy: Optional[str] = Opt(
            None,
            '-p', '--proxy',
            help='''Make Extractor requests via proxy: socks5://127.0.0.1:1080, http://user:passwd@127.0.0.1:443
NOTE: most sources works only in CIS and Baltic's region
''',
            show_default=False,
        ),
        m3u_size: int = Opt(
            6,
            '--m3u-size',
            help="generate playlist size. for MPV player"
        ),
        player_args: str = Opt('',
                               '-pa', '--player-args',
                               help='Extra mpv player arguments. should be wrap a double quotes (") '
                                    'and commands separate by single space ',
                               show_default=False)
):
    """base options"""
    ctx.ensure_object(dict)

    ctx.obj.update(
        {'source': source,
         'quality': quality,
         'proxy': proxy,
         'm3u_size': m3u_size,
         'player_args': player_args
         }
    )


@APP.command(name='min')
def min_cli(ctx: typer.Context):
    """primitive build-in realization. Based on standard input(). Minimal dependencies and features"""
    from anicli.min import main
    main(ctx.obj)


@APP.command(epilog="Old realisation. based on prompt-toolkit")
def eggella(ctx: typer.Context):
    """run old cli interface based on prompt-toolkit"""
    try:
        from anicli.eggella.main import app
    except ImportError as e:
        # if 'eggella' in e.msg or 'prompt-toolkit' in e.msg:
        #     raise ImportError('eggella dependency required: pip install anicli[eggella]') from e
        raise e
    # TODO: provide args
    app.loop()


@APP.command()
def textual(ctx: typer.Context):
    """run textual cli interface"""
    try:
        from anicli.tui.main import AnicliRuTui
    except ImportError as e:
        if 'textual' in e.msg:
            raise ImportError('textual dependency required: pip install anicli-ru[textual]') from e
        raise e
    # todo: provide args
    ctx: 'TYPER_CONTEXT_OPTIONS' = typer.get
    tui_app = AnicliRuTui()
    try:
        tui_app.run()
    finally:
        tui_app.mpv_ipc_socket.terminate()


@APP.command(epilog='WARNING: not recommended for production. This client not implemented security checks, '
                    'databases, cache, sessions and other features')
def web(ctx: typer.Context,
        host: A[str, Opt(help='serve host. default localhost')] = '127.0.0.1',
        port: A[int, Opt(help='server port')] = 10007,
        debug: bool = Opt(True, help='show debug messages')
        ):
    """run web interface (EXPERIMENTAL, UNSTABLE)"""
    ctx.obj: TYPER_CONTEXT_OPTIONS

    try:
        from anicli.web.main import app
    except ImportError as e:
        if 'flask' in e.msg:
            raise ImportError('web dependency required: pip install anicli-ru[web]') from e
        raise e

    # TODO: video reverse proxy implementation
    if ctx.obj['source'] in {'animego', 'jutsu'}:
        warnings.warn("current version not supports a provide headers to video stream. aniboom, "
                      "jutsu players don't work yet",
                      category=FutureWarning
                      )
    app.config['cli_args'] = ctx.obj
    app.run(host=host, port=port, debug=debug)


def run_cli():
    APP()
