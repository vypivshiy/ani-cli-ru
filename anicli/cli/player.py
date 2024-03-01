import os
import subprocess
import tempfile
import warnings
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Optional, List

from anicli_api.tools import generate_playlist

from anicli.log import logger
from anicli.utils import sanitize_filename

if TYPE_CHECKING:
    from anicli_api.player.base import Video


class BasePlayer:
    @classmethod
    @abstractmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None,
             **kwargs):
        pass

    @classmethod
    @abstractmethod
    def play_from_playlist(cls, videos: List["Video"], names: List[str], headers: Optional[dict] = None,
                           quality: int = 1080):
        pass

    @staticmethod
    def quote(arg: str) -> str:
        return f'"{sanitize_filename(arg)}"'

    @staticmethod
    def shell_execute(cmd: str):
        logger.debug("Executing: %s", cmd)
        if os.name == "nt":
            proc = subprocess.Popen(cmd)
        else:
            proc = subprocess.Popen(cmd, shell=True)
        proc.wait()


class MpvPlayer(BasePlayer):
    PLAYER = "mpv"
    TITLE = '--title'
    HEADERS_KEY = '--http-header-fields'
    USER_AGENT_KEY = '--user-agent'

    @classmethod
    def play_from_playlist(cls,
                           videos: List["Video"],
                           names: List[str],
                           headers: Optional[dict] = None,
                           quality: int = 1080):

        # TODO pass headers args from argument
        headers = videos[0].headers
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.m3u') as temp_file:
            playlist = generate_playlist(videos, names, quality=quality)
            temp_file.write(playlist)
        header_args = cls._parse_headers_args(headers) if headers else ""
        command = f'{cls.PLAYER} "{temp_file.name}" {header_args}'
        try:
            cls.shell_execute(command)
        finally:
            temp_file.close()

    @classmethod
    def _parse_headers_args(cls, headers: dict[str, Any]):
        if not headers:
            return ""
        # multiple command key build List Options:
        # shlex don't support mpv list arguments feature
        # Note:
        #       don't need whitespace see: man mpv, \http-header-fields
        #                                 v
        # --http-header-fields="Spam: egg","Foo: bar","BAZ: ZAZ"
        comma = f"{cls.HEADERS_KEY}="
        comma_user_agent = None

        for k, v in headers.items():
            if k.lower() == 'user-agent':
                comma_user_agent = f'{cls.USER_AGENT_KEY}="{v}"'
                headers.pop(k)
                if not headers:
                    return comma_user_agent

                break

        comma = comma + ','.join(f'"{k}: {v}"' for k, v in headers.items())
        return comma_user_agent + ' ' + comma if comma_user_agent else comma

    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None,
             **kwargs):
        title_arg = f'{cls.TITLE}={cls.quote(title)}' if title else ""
        headers_arg = cls._parse_headers_args(video.headers)
        command = f'{cls.PLAYER} {title_arg} {headers_arg} "{video.url}"'
        cls.shell_execute(command)


class VLCPlayer(BasePlayer):
    TITLE_ARG = '--meta-title'
    PLAYER = "vlc"

    @classmethod
    def play_from_playlist(cls, videos: List["Video"], names: List[str], headers: Optional[dict] = None,
                           quality: int = 1080):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.m3u') as temp_file:
            if videos[0].headers:
                warnings.warn(
                    "vlc player is not support set http headers", category=UserWarning
                )
                return
            playlist = generate_playlist(videos, names, quality=quality)
            temp_file.write(playlist)
            command = f'{cls.PLAYER} "{temp_file.name}"'

        try:
            cls.shell_execute(command)
        finally:
            temp_file.close()

    @classmethod
    def play(cls, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None,
             stdin: Optional[str] = None, **kwargs):
        if video.headers:
            warnings.warn(
                "vlc player is not support set http headers, usage --ffmpeg proxy instead", category=UserWarning
            )
            return
        title_arg = f'{cls.TITLE_ARG} {cls.quote(title)}' if title else ""

        cmd = f'vlc {title_arg} "{video.url}"'
        cls.shell_execute(cmd)


class CVLCPlayer(VLCPlayer):
    PLAYER = "cvlc"


class FFMPEGRouter(BasePlayer):
    """ffmpeg router for redirect video bytes to player by shell pipe `|`

    useful, if player not support http headers arguments
    """

    LOGLEVEL_ARG = "-loglevel error"

    URL_ARG = '-i "{}"'
    HLS_ARGS = (
        "-c copy -f hls -hls_flags append_list+omit_endlist " "-hls_segment_type mpegts -hls_playlist_type vod pipe:1"
    )
    PLAYER_ARG = "| {} {} -"
    HEARERS_ARG = "-headers "

    @classmethod
    def play_from_playlist(cls, videos: List["Video"], names: List[str], headers: Optional[dict] = None,
                           quality: int = 1080):
        raise NotImplementedError("Not supported m3u playlist")

    @classmethod
    def _headers(cls, headers: dict):
        if headers:
            arg = f'{cls.HEARERS_ARG}"'
            for k, v in headers.items():
                arg += f'{k}: {v}\n'
            return f'{arg}" '
        return ""

    @classmethod
    def play(
            cls,
            video: "Video",
            title: Optional[str] = None,
            player: Optional[str] = None,
            title_arg: Optional[str] = None,
            **kwargs,
    ):
        # todo add title argument
        headers_arg = cls._headers(video.headers)
        url = cls.URL_ARG.format(video.url)
        title_arg = title_arg.format(title) if title_arg and title else ""

        cmd = (
            f'ffmpeg '
            f'{cls.LOGLEVEL_ARG} {headers_arg} {url} {cls.HLS_ARGS} {cls.PLAYER_ARG.format(player, title_arg)}'
        )
        subprocess.Popen(cmd, shell=True).wait()


def run_video(video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, use_ffmpeg: bool = False):
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


def run_m3u_playlist(videos: List["Video"], names: List[str], quality: int = 1080):
    MpvPlayer.play_from_playlist(videos, names, quality=quality)
