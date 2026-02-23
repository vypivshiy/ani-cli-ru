"""AniCli - Anime CLI and Web Interface"""

from importlib.metadata import version

__version__ = version("anicli-ru")


def run_cli():
    """Entry point for CLI application"""
    from anicli.main import main # noqa
    main()
