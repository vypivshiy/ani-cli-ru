import webbrowser
from typing import List

from anicli_api.base import BaseOngoing, BaseEpisode, BaseSource
from anicli_api.source.animego import Extractor
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Input, Button, ListView

from anicli import tooltips as _
from .components import AppHeader, AnimeListItem
from .player.mpv import run_video
from .screens import AnimeResultScreen, SearchResultScreen, SourceResultScreen, VideoResultScreen
from ..utils.cached_extractor import CachedExtractor


class AnicliRuTui(App):
    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+b", "pop_screen", "back to previous screen"),
        ("ctrl+h", "help_screen", "show help page"),
        # ("ctrl+s", "toggle_sidebar", "Toggle sidebar")
    ]
    CSS_PATH = 'tui.css'

    ongoings: reactive[List[BaseOngoing]] = reactive([])
    extractor: reactive[CachedExtractor] = reactive(CachedExtractor(Extractor()))  # todo: choice source

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_ongoings()
        self.query_one('#ongoing-container').border_title = 'Ongoings'
        self.query_one('#ongoing-container').tooltip = _.APP_ONGOING_CONTAINER

        self.query_one('#search-container').border_title = 'Search or filter ongoings'

        self.query_one('#search-input').tooltip = _.APP_SEARCH_INPUT

    @work(exclusive=True)
    async def update_ongoings(self) -> None:
        ongs_view = self.query_one('#ongoings-items', ListView)

        self.query_one('#search-input').disabled = True
        ongs_view.loading = True
        self.ongoings = await self.extractor.a_ongoing()
        await ongs_view.extend([AnimeListItem(i, o) for i, o in enumerate(self.ongoings, 1)])

        self.query_one('#search-input').disabled = False
        ongs_view.loading = False

    def compose(self) -> ComposeResult:
        yield AppHeader(id='header')
        with Vertical():
            with Horizontal(id='search-container'):
                yield Input(placeholder='>', id='search-input')
                yield Button('Search', id='search-button')
            with Vertical(id='ongoing-container'):
                yield ListView(id='ongoings-items')
        yield Footer()

    @on(Button.Pressed, '#search-button')
    async def spawn_search_screen(self, _: Button.Pressed):
        value = self.query_one('#search-input', Input).value
        await self._spawn_search_screen(value)

    @on(Input.Submitted, '#search-input')
    async def search_results(self, event: Input.Submitted):
        value = event.value
        await self._spawn_search_screen(value)

    async def _spawn_search_screen(self, value: str):
        if not value:
            self.notify('Empty search query', severity='error')
            return

        self.query_one('#search-input').loading = True
        results = await self.extractor.a_search(value)
        if not results:
            self.notify(f'titles by [b]{value}[/b] query not founded', severity='error')
            self.query_one('#search-input').loading = False
            return

        self.query_one('#search-input').loading = False
        await self.push_screen(SearchResultScreen(search_results=results))

    @on(Input.Changed, '#search-input')
    async def on_input_changed(self, event: Input.Changed):
        """reuse search input via filter ongoings list"""
        list_view: ListView = self.query_one('#ongoings-items', ListView)
        ongoings = await self.extractor.a_ongoing()

        if not event.value:
            await list_view.clear()
            await list_view.extend([AnimeListItem(i, o) for i, o in enumerate(ongoings, 1)])
            return

        await list_view.clear()
        await list_view.extend(
            [AnimeListItem(i, o) for i, o in enumerate(ongoings, 1) if event.value.lower() in str(o).lower()])

    @on(ListView.Selected, '#ongoings-items, #search-items')
    async def ongoing_or_search_choice(self, event: ListView.Selected):
        event.list_view.loading = True
        result: SEARCH_OR_ONGOING = event.item.value  # type: ignore

        anime = await self.extractor.a_get_anime(result)
        episodes = await self.extractor.a_get_episodes(anime)
        if not episodes:
            self.notify(f'[bold]{anime.title}[/]: episodes not founded', severity='error')
            event.list_view.loading = False
            return

        event.list_view.loading = False
        await self.push_screen(AnimeResultScreen(anime, episodes))

    @on(ListView.Selected, '#list-pager')
    async def on_selected_list(self, event: ListView.Selected) -> None:
        event.list_view.loading = True
        ep: BaseEpisode = event.item.value

        sources = await self.extractor.a_get_sources(ep)

        if not sources:
            self.notify('Not found (maybe episode not released yet?)')
            event.item.loading = False
            return

        event.list_view.loading = False
        await self.push_screen(SourceResultScreen(sources))

    @on(ListView.Selected, '#source-items')
    async def get_videos(self, event: ListView.Selected):
        event.list_view.loading = True
        source: BaseSource = event.item.value

        videos = await self.extractor.a_get_videos(source)

        event.list_view.loading = False
        await self.push_screen(VideoResultScreen(videos))

    @on(Button.Pressed, '.back-source, .back-search, .back-anime, .back-video')
    async def pop_screen_button_click(self):
        await self.pop_screen()

    @on(ListView.Selected, '#video-items')
    async def play_video(self, event: ListView.Selected):
        video = event.item.value
        event.list_view.loading = True

        self.notify(f'run video {video}')

        self._play_video(video)
        event.list_view.loading = False

    @work(thread=True)
    def _play_video(self, video):
        run_video(video)

    def action_open_page(self, url: str):
        webbrowser.open(url)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_pop_screen(self):
        if len(self.screen_stack) == 1:
            return
        self.pop_screen()


if __name__ == '__main__':
    AnicliRuTui().run()
