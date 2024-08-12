from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer
from textual.screen import Screen

from ..components import new_list_view, ButtonPopScreen

if TYPE_CHECKING:
    from ...utils.cached_extractor import CachedItemAsyncContext


class SearchResultScreen(Screen):
    def __init__(self, context: 'CachedItemAsyncContext'):
        super().__init__()
        self.context = context

    def on_mount(self):
        self.query_one('#search-results-container').border_title = 'Search results'

    def compose(self) -> ComposeResult:
        with Vertical(id='search-results-container'):
            yield new_list_view(
                self.context.searches_or_ongoings,
                id='search-items')
            yield ButtonPopScreen('back-search')
        yield Footer()
