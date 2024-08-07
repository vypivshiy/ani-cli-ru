from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from typing import TYPE_CHECKING
from ..components import new_list_view, MiddleTitle, ButtonPopScreen
from ...types_ import LIST_SEARCH_OR_ONGOING

if TYPE_CHECKING:
    from ...utils.cached_extractor import CachedItemContext


class SearchResultScreen(Screen):
    def __init__(self, context: 'CachedItemContext'):
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
