from typing import TYPE_CHECKING, List

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import TextArea

from ..components import MiddleTitle, ButtonPopScreen, new_list_paginator

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseEpisode


class AnimeResultScreen(Screen):
    DEFAULT_CSS = """
    #episodes-header {
        content-align: center middle;
    }
    /* eg comment */
    #episode-items {
        height: 30%;
    }
    """

    def __init__(self,
                 anime: 'BaseAnime',
                 episodes: List['BaseEpisode']
                 ):
        super().__init__()
        self.episodes = episodes
        self.anime = anime

    def on_mount(self):
        self.query_one('#anime-result-container').border_title = self.anime.title
        self.query_one('#episode-items').border_title = 'Episodes'

    def compose(self) -> ComposeResult:
        with Vertical(id='anime-result-container'):
            yield TextArea(self.anime.description, id='anime-descr', read_only=True, tab_behavior='indent')
            yield new_list_paginator(self.episodes, id='episode-items')
            yield ButtonPopScreen('back-anime')
