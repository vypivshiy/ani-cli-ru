from typing import TYPE_CHECKING, Union

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Button

from .consts import LOGO_HEADER

if TYPE_CHECKING:
    from rich.console import ConsoleRenderable, RichCast


def ButtonPopScreen(classes: str):
    """global shortcuts for helps pop screens"""
    return Button('Back', classes=classes)


class MiddleTitle(Static):
    DEFAULT_CSS = """
        .middle-title {
            content-align: center middle;
            border: solid;
        }
        """

    def __init__(self, renderable: Union['ConsoleRenderable', 'RichCast', str], classes: str = 'middle-title',
                 **kwargs):
        super().__init__(**kwargs, classes=classes)
        self.renderable = renderable

    def compose(self) -> ComposeResult:
        yield Static(self.renderable)


class AppHeader(Horizontal):
    LOGO = LOGO_HEADER
    DEFAULT_CSS = """
    #header-logo {
        border: solid blue;
        }
    """

    def compose(self):
        yield Static(self.LOGO, id='header-logo')
