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
    TITLE = '--title'
    HEADERS_KEY = '--http-header-fields'

    @classmethod
    def _parse_headers_args(cls, headers: dict[str, Any]):
        if not headers:
            return ""
        # multiple command key build List Options:
        # Note:
        #       don't need whitespace see: man mpv, \http-header-fields
        #                                 v
        # --http-header-fields="Spam: egg","Foo: bar","BAZ: ZAZ"
        comma = f"{cls.HEADERS_KEY}="

        for k, v in headers.items():
            comma+= f'"{k}: {v}",'

        return comma.rstrip(',')

    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        _args = [cls.PLAYER]

        title_arg = f'{cls.TITLE}="{repr(title)[1:-1]}"'  if title else ""
        headers_arg = cls._parse_headers_args(video.headers)

        command = f'{cls.PLAYER} {title_arg} {headers_arg} "{video.url}"'
        print(command)
        subprocess.Popen(command, shell=True).wait()


class VLCPlayer(BasePlayer):
    TITLE_ARG = '--meta-title'

    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        if video.headers:
            warnings.warn("vlc player is not support set http headers, usage --ffmpeg proxy instead",
                          category=UserWarning)
            return
        title_arg = f'{cls.TITLE_ARG} "{repr(title)[1:-1]}"' if title else ""

        cmd = f'vlc {title_arg} "{video.url}"'
        subprocess.Popen(cmd, shell=True).wait()


class CVLCPlayer(VLCPlayer):
    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        if video.headers:
            warnings.warn("vlc player is not support set http headers, usage --ffmpeg key instead", stacklevel=3)
            return
        title_arg = f'{cls.TITLE_ARG} "{repr(title)[1:-1]}"' if title else ""

        cmd = f'cvlc {title_arg} "{video.url}"'
        subprocess.Popen(cmd, shell=True).wait()


class FFMPEGRouter(BasePlayer):
    """ffmpeg router for redirect video bytes to player by shell pipe `|`

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
        subprocess.Popen(cmd, shell=True).wait()


def run_video(video: "Video",
              title: Optional[str] = None, *,
              player: Optional[str] = None,
              use_ffmpeg: bool = False):
    if use_ffmpeg:
        if player == "mpv":
            FFMPEGRouter.play(video, title, player=player, title_arg='--tit le="{}"')
        elif player in ("vlc", "cvlc"):
            FFMPEGRouter.play(video, title, player=player, title_arg='--meta-title "{}"')
        return
    elif player == "mpv":
        return MpvPlayer.play(video, title)
    elif player == "vlc":
        return VLCPlayer.play(video, title)
