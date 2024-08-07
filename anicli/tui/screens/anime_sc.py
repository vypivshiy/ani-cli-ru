from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import TextArea, Button, SelectionList

from ..components import ButtonPopScreen
from ..components.episodes_selector import EpisodesSelector

if TYPE_CHECKING:
    from ...utils.cached_extractor import CachedItemContext


class AnimeResultScreen(Screen):
    def __init__(self, context: 'CachedItemContext'):
        super().__init__()
        self.context = context

    def on_mount(self):
        self.query_one('#anime-result-container').border_title = self.context.anime.title
        self.query_one('#episodes-items').border_title = 'Episodes'

    def compose(self) -> ComposeResult:
        with Vertical(id='anime-result-container'):
            yield TextArea(self.context.anime.description,
                           id='anime-descr',
                           read_only=True,
                           tab_behavior='indent')
            yield EpisodesSelector(self.context.episodes, id='episodes-selector')
            yield ButtonPopScreen('back-anime')

