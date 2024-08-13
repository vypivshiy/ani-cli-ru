import webbrowser
from typing import List

from anicli_api.base import BaseOngoing, BaseEpisode, BaseSource
from anicli_api.source.animego import Extractor
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Input, Button, ListView, SelectionList

from anicli import tooltips as _
from anicli.libs.mpv_json_ipc import MPV
from anicli.tui.components.utils import set_loading, update_list_view
from anicli.tui.screens.player_sc import MPVPlayerSc
from .components import AppHeader, AnimeListItem
from .screens import AnimeResultScreen, SearchResultScreen, SourceResultScreen, VideoResultScreen
from ..utils.cached_extractor import CachedExtractorAsync, CachedItemAsyncContext


class _ActionsAppMixin(App):

    @staticmethod
    def action_open_page(url: str):
        webbrowser.open(url)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark  # type: ignore

    def action_pop_screen(self):
        if len(self.screen_stack) == 1:
            return

        # bind close video shortcut
        if isinstance(self.screen_stack[-1], MPVPlayerSc):
            try:
                self.screen_stack[-1].mpv_socket.command('stop')
            except BrokenPipeError:
                pass
        self.pop_screen()


class AnicliRuTui(_ActionsAppMixin, App):
    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+b", "pop_screen", "back to previous screen"),
        ("ctrl+h", "help_screen", "show help page"),
    ]
    CSS_PATH = 'tui.css'

    ongoings: List[BaseOngoing] = reactive([])
    # todo: choice extractor source
    cached_extractor: CachedExtractorAsync = reactive(CachedExtractorAsync(Extractor()))

    def __init__(self, extractor=Extractor()):
        super().__init__()
        self.cached_extractor = CachedExtractorAsync(extractor)
        self.context = CachedItemAsyncContext(extractor=self.cached_extractor)
        self.mpv_ipc_socket = MPV()

    def on_mount(self) -> None:
        self.update_ongoings()
        self.query_one('#ongoing-container').border_title = 'Ongoings'
        self.query_one('#ongoing-container').tooltip = _.APP_ONGOING_CONTAINER
        self.query_one('#search-container').border_title = 'Search or filter ongoings'
        self.query_one('#search-input').tooltip = _.APP_SEARCH_INPUT

    # BASE APP LAYER
    @work(exclusive=True)
    async def update_ongoings(self) -> None:
        ongoings_lv = self.query_one('#ongoings-items', ListView)
        self.query_one('#search-input').disabled = True

        with set_loading(ongoings_lv):
            self.ongoings = await self.context.a_ongoing()
            await ongoings_lv.extend([AnimeListItem(i, o) for i, o in enumerate(self.ongoings, 1)])
            self.query_one('#search-input').disabled = False

    def compose(self) -> ComposeResult:
        yield AppHeader(id='header')
        with Vertical():
            with Horizontal(id='search-container'):
                yield Input(placeholder='>', id='search-input')
            with Vertical(id='ongoing-container'):
                yield ListView(id='ongoings-items')
        yield Footer()

    @on(Input.Submitted, '#search-input')
    async def on_input_submit_search(self, event: Input.Submitted):
        value = event.value
        if not value:
            self.notify('Empty search query', severity='error')
            return

        with set_loading(self.query_one('#search-input')):
            results = await self.context.a_search(value)
            if not results:
                self.notify(f'Titles by [b]{value}[/b] query not founded', severity='error')
                return
            await self.push_screen(SearchResultScreen(self.context))

    @on(Input.Changed, '#search-input')
    async def on_input_ongoings_filter(self, event: Input.Changed):
        # reuse search input via filter ongoings list
        list_view: ListView = self.query_one('#ongoings-items', ListView)
        ongoings = await self.context.a_ongoing()

        if not event.value:
            new_items = (AnimeListItem(i, o) for i, o in enumerate(ongoings, 1))
            update_list_view(list_view, *new_items)
            return

        new_items = (AnimeListItem(i, o) for i, o in enumerate(ongoings, 1)
                     if event.value.lower() in str(o).lower())
        update_list_view(list_view, *new_items)

    # SEARCH + ONGOINGS
    @on(ListView.Selected, '#ongoings-items, #search-items')
    async def on_lv_select_spawn_anime_sc(self, event: ListView.Selected):
        with set_loading(event.list_view):
            result: SEARCH_OR_ONGOING = event.item.value  # type: ignore
            anime = await self.context.a_get_anime(result)
            episodes = await self.context.a_get_episodes()

            if not episodes:
                self.notify(f'[bold]{anime.title}[/]: episodes not founded', severity='error')
                return
        await self.push_screen(AnimeResultScreen(self.context))

    # ANIME SCREEN
    @on(ListView.Selected, '#list-pager')
    async def on_lv_select_push_source_sc(self, event: ListView.Selected) -> None:
        with set_loading(event.list_view, event.item):
            ep: BaseEpisode = event.item.value  # type: ignore
            sources = await self.context.a_get_sources(ep)
            if not sources:
                self.notify('Not found (maybe episode not released yet?)')
                return

        await self.push_screen(SourceResultScreen(self.context))

    @on(Button.Pressed, '#episodes-pick-accept')
    async def episodes_choice_accept(self, _):
        episodes_indexes = self.query_one('#episodes-items', SelectionList).selected
        if len(episodes_indexes) == 0:
            self.notify('Please, choice episodes')
            return

        self.context.picked_episode_indexes = episodes_indexes
        # pick first sources list. slice playlist logic calculate be later
        self.context.sources = await self.cached_extractor.a_get_sources(
            self.context.episodes[episodes_indexes[0]]
        )
        # ongoings case:
        # check last episode index if exist and check available videos
        max_ep_index = max(self.context.picked_episode_indexes)
        if max_ep_index == len(self.context.episodes) - 1:
            result = await self.context.a_get_sources(self.context.episodes[-1])
            if not result:
                self.notify('last episode is not available. Maybe it release later?',
                            severity='warning'
                            )
                return

        await self.push_screen(SourceResultScreen(self.context))

    # SOURCE SCREEN
    @on(ListView.Selected, '#source-items')
    async def on_lv_selected_push_video_sc(self, event: ListView.Selected):
        with set_loading(event.list_view, event.item):
            source: BaseSource = event.item.value  # type: ignore
            self.context.picked_source = source
            videos = await self.context.a_get_videos(source)
            if not videos:
                self.notify('Not found videos')
                return
            self.context.videos = videos

        await self.push_screen(VideoResultScreen(self.context))

    # VIDEO SCREEN
    @on(ListView.Selected, '#video-items')
    async def on_lv_select_play_video(self, event: ListView.Selected):
        with set_loading(event.list_view):
            video = event.item.value  # type: ignore
            self.context.picked_video = video

            await self.push_screen(
                MPVPlayerSc(self.context, self.mpv_ipc_socket)
            )

    def _init_mpv_socket(self):

        self.mpv_ipc_socket = MPV()
        # TODO
        # for p in self.MPV_PROPERTIES_LOG:
        #     self.mpv_ipc_socket.bind_property_observer(p, self.handle_observer)

    @on(Button.Pressed, '.back-source, .back-search, .back-anime, .back-video')
    async def on_button_pop_sc(self):
        """universal close screen entrypoint"""
        await self.pop_screen()

    @on(Button.Pressed, '.back-player')
    async def close_video(self):

        sc: MPVPlayerSc = self.screen_stack[-1]  # type: ignore
        try:
            sc.mpv_socket.command('stop')
        except BrokenPipeError:
            # mpv closed manually, ignore exception
            pass

        finally:
            await self.pop_screen()


if __name__ == '__main__':
    AnicliRuTui().run()
