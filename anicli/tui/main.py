import webbrowser
from typing import List

from anicli_api.base import BaseOngoing, BaseEpisode, BaseSource
from anicli_api.source.animego import Extractor
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Static, Input, Button, ListView, LoadingIndicator

from anicli2.tui.screens import AnimeResultScreen, SearchResultScreen, SourceResultScreen
from anicli2.utils.cached_extractor import CachedExtractor
from .widgets import AppHeader, AnimeListItem


class AnicliRuTui(App):
    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        # ("ctrl+s", "toggle_sidebar", "Toggle sidebar")
    ]
    CSS_PATH = 'tui.css'

    ongoings: reactive[List[BaseOngoing]] = reactive([])
    extractor: reactive[CachedExtractor] = reactive(CachedExtractor(Extractor()))  # todo: choice source

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_ongoings()

    @work(exclusive=True)
    async def update_ongoings(self) -> None:
        self.ongoings = await self.extractor.a_ongoing()
        ongs_view = self.query_one('#ongoings-items', ListView)
        await ongs_view.extend([AnimeListItem(i, o) for i, o in enumerate(self.ongoings, 1)])

        loading_ico = self.query_one('#ongoings-loads', LoadingIndicator)
        loading_ico.styles.display = 'none'

    def compose(self) -> ComposeResult:
        yield AppHeader(id='header')
        with Vertical():
            with Horizontal(id='search-container'):
                yield Input(placeholder='search|filter ongoings >', id='search-input')
                yield Button('Search', id='search-button')
            with Vertical(id='ongoings-container'):
                yield Static("Ongoings", id='ongoings-header')
                yield LoadingIndicator(id='ongoings-loads')
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

        results = await self.extractor.a_search(value)
        if not results:
            self.notify(f'titles by [b]{value}[/b] query not founded', severity='warning')
            return

        await self.push_screen(SearchResultScreen(extractor=self.extractor, search_results=results))

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
        result: SEARCH_OR_ONGOING = event.item.value  # type: ignore
        anime = await self.extractor.a_get_anime(result)
        episodes = await anime.a_get_episodes()
        if not episodes:
            self.notify(f'Episodes not found in [bold]{anime.title}[/]', severity='error')
            return
        await self.push_screen(AnimeResultScreen(self.extractor, anime, episodes))

    @on(ListView.Selected, '#list-pager')
    async def on_selected_list(self, event: ListView.Selected) -> None:
        ep: BaseEpisode = event.item.value
        self.notify(f'picked {event.item.value}')
        sources = await ep.a_get_sources()
        if not sources:
            self.notify('Not found (maybe episode not released already?)')
            return

        await self.push_screen(SourceResultScreen(self.extractor, sources))

    @on(ListView.Selected, '#source-items')
    async def get_videos(self, event: ListView.Selected):
        source: BaseSource = event.item.value
        videos = await self.extractor.a_get_videos(source)
        self.notify(f'picked {event.item.value}')

    @on(Button.Pressed, '#search-close, #anime-close, #source-back')
    async def _pop_search_screen(self):
        # HACK: clear input in main screen
        # self.query_one('#search-input', Input).clear()
        await self.pop_screen()

    def action_open_page(self, url: str):
        webbrowser.open(url)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == '__main__':
    AnicliRuTui().run()
