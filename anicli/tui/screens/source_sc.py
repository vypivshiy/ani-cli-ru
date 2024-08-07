from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen

from ..components import new_list_view, ButtonPopScreen

if TYPE_CHECKING:
    from ...utils.cached_extractor import CachedItemContext


class SourceResultScreen(Screen):

    def __init__(self, context: 'CachedItemContext'):
        super().__init__()
        self.context = context

    def on_mount(self):
        self.query_one('#sources-result-container').border_title = 'Choice source|dubber'
        self.query_one('#sources-result-container').tooltip = \
            'The source you select will determine how subsequent videos will be played.'

    def compose(self) -> ComposeResult:
        with VerticalScroll(id='sources-result-container'):
            yield new_list_view(self.context.sources, id='source-items')
            yield ButtonPopScreen('back-source')
