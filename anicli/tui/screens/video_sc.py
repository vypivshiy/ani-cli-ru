from typing import List, TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer
from ..components import new_list_view, ButtonPopScreen

if TYPE_CHECKING:
    from ...utils.cached_extractor import CachedItemContext


class VideoResultScreen(Screen):
    def __init__(self, context: 'CachedItemContext'):
        super().__init__()
        self.context = context

    def on_mount(self):
        self.query_one('#sources-videos-container').border_title = 'Choice video'

    def compose(self) -> ComposeResult:
        with VerticalScroll(id='sources-videos-container'):
            yield new_list_view(self.context.videos, id='video-items')
            yield ButtonPopScreen('back-video')
        yield Footer()
