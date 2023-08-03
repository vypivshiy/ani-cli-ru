import warnings
from abc import abstractmethod
from contextlib import suppress

from typing import TYPE_CHECKING, Any, Optional
import subprocess

if TYPE_CHECKING:
    from anicli_api.player.base import Video


class BasePlayer:
    @classmethod
    @abstractmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        pass


class MpvPlayer(BasePlayer):
    PLAYER = "mpv"
    TITLE = '--title="{}"'
    HEADERS = '--http-header-fields="{key}: {value}" '

    @classmethod
    def _parse_headers_args(cls, headers: dict[str, Any]):
        comma = ""
        for k, v in headers.items():
            comma += cls.HEADERS.format(key=k, value=v)
            comma += " "
        return comma

    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        title_arg = cls.TITLE.format(title) if title else ""
        headers_arg = cls._parse_headers_args(video.headers)
        subprocess.Popen(f'{cls.PLAYER} {title_arg} {headers_arg} "{video.url}"', shell=True).wait()


class VLCPlayer(BasePlayer):
    TITLE_ARG = '--meta-title "{}"'

    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        if video.headers:
            warnings.warn("vlc player is not support set http headers, usage --ffmpeg key instead", stacklevel=3)
            return
        title_arg = cls.TITLE_ARG.format(title) if title else ""
        cmd = f'vlc {title_arg} "{video.url}"'
        subprocess.Popen(cmd, shell=True).wait()


class CVLCPlayer(VLCPlayer):
    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        if video.headers:
            warnings.warn("vlc player is not support set http headers, usage --ffmpeg key instead", stacklevel=3)
            return
        title_arg = cls.TITLE_ARG.format(title) if title else ""
        cmd = f'cvlc {title_arg} "{video.url}"'
        subprocess.Popen(cmd, shell=True).wait()


class FFMPEGRouter(BasePlayer):
    """ffmpeg router for redirect video to players

    useful, if player not support http headers arguments
    """
    LOGLEVEL_ARG = "-loglevel error"
    URL_ARG = '-i "{}"'
    HLS_ARGS = "-c copy -f hls -hls_flags append_list+omit_endlist " \
               "-hls_segment_type mpegts -hls_playlist_type vod pipe:1"
    PLAYER_ARG = "| {} {} -"
    HEARERS_ARG = "-headers "

    @classmethod
    def _headers(cls, headers: dict):
        if headers:
            arg = f'{cls.HEARERS_ARG}"'
            for k, v in headers.items():
                arg += f'{k}: {v}\n'
            return f'{arg}" '
        return ""

    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None,
             player: Optional[str] = None, title_arg: Optional[str] = None, **kwargs):
        # todo add title argument
        headers_arg = cls._headers(video.headers)
        url = cls.URL_ARG.format(video.url)
        title_arg = title_arg.format(title) if title_arg and title else ""
        cmd = f'ffmpeg ' \
              f'{cls.LOGLEVEL_ARG} {headers_arg} {url} {cls.HLS_ARGS} {cls.PLAYER_ARG.format(player, title_arg)}'
        # print(cmd)
        subprocess.Popen(cmd, shell=True).wait()


def run_video(video: "Video",
              title: Optional[str] = None, *,
              player: Optional[str] = None,
              use_ffmpeg: bool = False):
    if use_ffmpeg:
        if player == "mpv":
            FFMPEGRouter.play(video, title, player=player, title_arg='--title="{}"')
        elif player in ("vlc", "cvlc"):
            FFMPEGRouter.play(video, title, player=player, title_arg='--meta-title "{}"')
        return
    elif player == "mpv":
        return MpvPlayer.play(video, title)
    elif player == "vlc":
        return VLCPlayer.play(video, title)
