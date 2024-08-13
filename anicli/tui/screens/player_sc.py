from anicli_api.tools.m3u import Playlist
from textual import work, on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Log, Button, Input, Label, ProgressBar

from anicli.libs.mpv_json_ipc import MPV, MPVError
from anicli.utils.cached_extractor import CachedItemAsyncContext
from ..utils.slice_playlist import new_tmp_playlist, make_playlist_items
from ...utils.str_formatters import float_to_hms


class MPVPlayerSc(Screen):
    # defaults mpv events handle
    MPV_PROPERTIES_LOG = [
        "playback-time", "pause", "volume", "duration",
        "playlist-pos",
        "chapter",
        "audio-bitrate",
    ]
    # get-property pause
    # set-property pause true
    # set-property pause false
    pause = var(False)
    # get-property volume
    volume = var(100)
    duration = var(None)
    """video duration trigger observer get-property duration"""

    playback_time = var(0)
    """video ETA trigger observer get-property playback-time"""
    # get-property playlist
    playlist_pos = var(None)
    playlist_max = var(0)
    # get-property media-title
    media_title = var(None)
    cache = var(None)

    def __init__(self,
                 context: 'CachedItemAsyncContext',
                 mpv_socket: 'MPV'):
        super().__init__()
        self.context = context

        self.mpv_socket = mpv_socket

    def compose(self) -> ComposeResult:
        yield Button('Close', classes='back-player')
        yield Label('', id='media-title')
        yield Label('', id='playlist-pos')
        with Horizontal():
            yield Label('--:--:--', id='video-pos-start')
            yield ProgressBar(id='video-progress', show_eta=False, show_percentage=False)
            yield Label('--:--:--', id='video-pos-end')
        with Vertical():
            yield Input(placeholder='mpv cmd >', id='mpv-cmd', suggester=start_suggester)
        yield Log(id='player-logs')

    def on_mount(self):
        for prop in self.MPV_PROPERTIES_LOG:
            self.mpv_socket.bind_property_observer(prop, self.handle_observer)

        self.run_video()

    @on(Input.Submitted, '#mpv-cmd')
    def mpv_exec(self, ev: Input.Submitted):
        try:
            MAPPING = {'true': True, 'false': False}

            cmd, *args = ev.value.split(' ')
            args = tuple(MAPPING.get(arg, arg) for arg in args)
            data = self.mpv_socket.command(cmd, *args)
            self.query_one('#player-logs', Log).write_line(f'EXEC -> {data}')

        except MPVError as e:
            self.query_one('#player-logs', Log).write_line(f'ERROR -> {e}')

    @work(exclusive=True)
    async def run_video(self):
        playlist_items = await make_playlist_items(self.context)
        self.playlist_max = len(playlist_items[0])

        playlist = Playlist.from_videos(*playlist_items)
        with new_tmp_playlist(playlist) as pl_file:
            self.mpv_socket.play(pl_file)

    def watch_duration(self, value):
        if value:
            self.query_one('#video-pos-end', Label).update(float_to_hms(value))
            self.query_one('#video-progress', ProgressBar).total = int(value)

    def watch_playback_time(self, value):
        if value != None:
            self.query_one('#video-pos-start', Label).update(float_to_hms(value))
            self.query_one('#video-progress', ProgressBar).update(progress=int(value))

    def watch_media_title(self, value):
        if value:
            self.query_one('#media-title', Label).update(value)

    def watch_playlist_pos(self, value):
        if value != None:
            # self.mpv_socket.command('get-property', *['playlist',])
            self.query_one('#playlist-pos', Label).update(f'playlist-pos: {value + 1}|{self.playlist_max}')

    def handle_observer(self, key, data):
        # TODO: rewrite to reactive
        self.query_one('#player-logs', Log).write_line(f'{key} -> {data}')
        if key == 'duration' and data:
            self.duration = int(data)
        elif key == 'playback-time' and data:
            self.playback_time = int(data)
        elif key == 'media-title':
            self.media_title = data
        elif key == 'playlist-pos':
            self.playlist_pos = data
