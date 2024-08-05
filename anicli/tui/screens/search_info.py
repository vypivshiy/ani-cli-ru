from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen

from ..components import new_list_view, MiddleTitle, ButtonPopScreen
from ...types_ import LIST_SEARCH_OR_ONGOING


class SearchResultScreen(Screen):
    def __init__(self, search_results: LIST_SEARCH_OR_ONGOING):
        super().__init__()
        self.search_results = search_results

    def on_mount(self):
        self.query_one('#search-results-container').border_title = 'Search results'

    def compose(self) -> ComposeResult:
        with Vertical(id='search-results-container'):
            yield new_list_view(
                self.search_results,
                id='search-items')
            yield ButtonPopScreen('back-search')
