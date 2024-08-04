from typing import List

from anicli_api.base import BaseAnime, BaseEpisode, BaseSource
from anicli_api.player.base import Video
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Label, TextArea, ListView, Button, Static, Input

from anicli2.tui.validators import InputPeekValidator
from anicli2.tui.widgets import AnimeListItem, ListPaginator
from anicli2.types_ import LIST_SEARCH_OR_ONGOING
from anicli2.utils.cached_extractor import CachedExtractor


class VideoResultScreen(Screen):
    def __init__(self, videos: List[Video]):
        super().__init__()
        self.videos = videos

    def compose(self) -> ComposeResult:
        yield Static('Sources:', id='source-title')
        yield ListView(*[AnimeListItem(i, s) for i, s in enumerate(self.videos, 1)],
                       id='video-items')
        yield Button('Back', id='source-back')


class SourceResultScreen(Screen):
    DEFAULT_CSS = """
        #source-title {
            content-align: center middle;
        }
        
        """

    def __init__(self, extractor: CachedExtractor, sources: List[BaseSource]):
        super().__init__()
        self.extractor = extractor
        self.sources = sources

    def compose(self) -> ComposeResult:
        yield Static('Sources:', id='source-title')
        yield ListView(*[AnimeListItem(i, s) for i, s in enumerate(self.sources, 1)],
                       id='source-items')
        yield Button('Back', id='source-back')



class AnimeResultScreen(Screen):
    DEFAULT_CSS = """
    #anime-title {
        content-align: center middle;
    }
    #episodes-header {
        content-align: center middle;
    }
    /* eg comment */
    #episode-items {
        height: 30%;
    }
    """

    def __init__(self,
                 extractor: CachedExtractor,
                 anime: BaseAnime,
                 episodes: List[BaseEpisode]
                 ):
        super().__init__()
        self.extractor = extractor
        self.episodes = episodes
        self.anime = anime

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.anime.title, id='anime-title')
            yield TextArea(self.anime.description, id='anime-descr', read_only=True, tab_behavior='indent')
            yield Label('Episodes', id='episodes-header')
            yield ListPaginator(*[AnimeListItem(i, e) for i, e in enumerate(self.episodes, 1)],
                                id='episode-items')
            yield Input(placeholder='take slice', id='episodes-filter', validators=InputPeekValidator(self.episodes))
            yield Button('Back', id='anime-close')


class SearchResultScreen(Screen):
    DEFAULT_CSS = """
    #search-title {
        content-align: center middle;
    }
    """

    def __init__(self, extractor: CachedExtractor, search_results: LIST_SEARCH_OR_ONGOING):
        super().__init__()
        self.extractor = extractor
        self.search_results = search_results

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Search Result", id='search-title')
            yield ListView(*[AnimeListItem(i, r) for i, r in enumerate(self.search_results, 1)], id='search-items')
            yield Button('Back', id='search-close')
