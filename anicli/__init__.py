"""AniCli - Anime CLI and Web Interface"""

from importlib.metadata import version

from anicli.main import main

__version__ = version("anicli-ru")


def run_cli():
    """Entry point for CLI application"""
    main()
