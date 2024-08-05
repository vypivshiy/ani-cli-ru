from typing import List, TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen

from ..components import new_list_view, ButtonPopScreen

if TYPE_CHECKING:
    from anicli_api.base import BaseSource
    from anicli_api.player.base import Video


class VideoResultScreen(Screen):
    def __init__(self, videos: List['Video']):
        super().__init__()
        self.videos = videos

    def on_mount(self):
        self.query_one('#sources-videos-container').border_title = 'Choice video:'

    def compose(self) -> ComposeResult:
        with VerticalScroll(id='sources-videos-container'):
            yield new_list_view(self.videos, id='video-items')
            yield ButtonPopScreen('back-video')


class SourceResultScreen(Screen):

    def __init__(self, sources: List['BaseSource']):
        super().__init__()
        self.sources = sources

    def on_mount(self):
        self.query_one('#sources-result-container').border_title = 'Sources'

    def compose(self) -> ComposeResult:
        with VerticalScroll(id='sources-result-container'):
            yield new_list_view(self.sources, id='source-items')
            yield ButtonPopScreen('back-source')
