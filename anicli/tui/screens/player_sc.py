from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Log

from anicli.tui.components import ButtonPopScreen
from anicli.utils.cached_extractor import CachedItemContext
from ..utils.slice_playlist import new_tmp_playlist, make_playlist
from ...mpv_json_ipc import MPV


class MPVPlayerSc(Screen):
    MPV_PROPERTIES_LOG = [
        "playback-time", "pause", "volume", "duration",
        "playlist-pos", "filename", "chapter", "audio-bitrate"
    ]

    def __init__(self, context: 'CachedItemContext'):
        super().__init__()
        self.context = context

        self.mpv_socket = self._init_mpv_socket()

    def compose(self) -> ComposeResult:
        yield ButtonPopScreen('back-player')
        yield Log(id='player-logs')

    def _init_mpv_socket(self):
        mpv = MPV()
        for p in self.MPV_PROPERTIES_LOG:
            mpv.bind_property_observer(p, self.handle_observer)
        return mpv

    def on_mount(self):
        self.run_video()

    @work(exclusive=True)
    async def run_video(self):
        playlist = await make_playlist(self.context)

        with new_tmp_playlist(playlist) as pl_file:
            try:
                # TODO: headers pass
                self.mpv_socket.play(pl_file)
            except BrokenPipeError:
                # if mpv closed manually or receive SIGKILL signal, create new
                self.mpv_socket = self._init_mpv_socket()
                self.mpv_socket.play(pl_file)

    def handle_observer(self, key, data):
        self.query_one('#logs-view', Log).write_line(f'{key} -> {data}')
