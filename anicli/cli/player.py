import os
import subprocess
import tempfile
import warnings
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from anicli_api.tools import generate_playlist

from anicli.log import logger
from anicli.utils import sanitize_filename

if TYPE_CHECKING:
    from anicli_api.player.base import Video

    from anicli.cli.config import Config


class BasePlayer:

    def __init__(self, app_cfg: "Config"):
        self.app_cfg = app_cfg

    @abstractmethod
    def play(self, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        pass

    @abstractmethod
    def play_from_playlist(
        self, videos: List["Video"], names: List[str], headers: Optional[Dict] = None, quality: int = 1080
    ):
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
    TITLE = "--title"
    HEADERS_KEY = "--http-header-fields"
    USER_AGENT_KEY = "--user-agent"

    def play_from_playlist(
        self, videos: List["Video"], names: List[str], headers: Optional[Dict] = None, quality: int = 1080
    ):

        # TODO pass headers args from argument
        headers = videos[0].headers
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".m3u") as temp_file:
            playlist = generate_playlist(videos, names, quality=quality)
            temp_file.write(playlist)
        header_args = self._parse_headers_args(headers) if headers else ""
        command = f'{self.PLAYER} "{temp_file.name}" {header_args}'
        try:
            self.shell_execute(command)
        finally:
            temp_file.close()

    @classmethod
    def _parse_headers_args(cls, headers: Dict[str, Any]):
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
            if k.lower() == "user-agent":
                comma_user_agent = f'{cls.USER_AGENT_KEY}="{v}"'
                headers.pop(k)
                if not headers:
                    return comma_user_agent

                break

        comma = comma + ",".join(f'"{k}: {v}"' for k, v in headers.items())
        return comma_user_agent + " " + comma if comma_user_agent else comma

    def play(self, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs):
        title_arg = f"{self.TITLE}={self.quote(title)}" if title else ""
        headers_arg = self._parse_headers_args(video.headers)
        extra_args = self.app_cfg.PLAYER_EXTRA_ARGS
        command = f'{self.PLAYER} {extra_args} {title_arg} {headers_arg} "{video.url}"'
        self.shell_execute(command)


class VLCPlayer(BasePlayer):
    TITLE_ARG = "--meta-title"
    PLAYER = "vlc"

    def play_from_playlist(
        self, videos: List["Video"], names: List[str], headers: Optional[Dict] = None, quality: int = 1080
    ):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".m3u") as temp_file:
            if videos[0].headers:
                warnings.warn("vlc player is not support set http headers", category=UserWarning)
                return
            playlist = generate_playlist(videos, names, quality=quality)
            temp_file.write(playlist)
            command = f'{self.PLAYER} "{temp_file.name}"'

        try:
            self.shell_execute(command)
        finally:
            temp_file.close()

    def play(
        self, video: "Video", title: Optional[str] = None, *, player: Optional[str] = None, **kwargs: Optional[str]  # noqa
    ):
        if video.headers:
            warnings.warn(
                "vlc player is not support set http headers, usage --ffmpeg proxy instead",
                category=RuntimeWarning,
                stacklevel=1
            )
            return
        title_arg = f"{self.TITLE_ARG} {self.quote(title)}" if title else ""
        extra_args = self.app_cfg.PLAYER_EXTRA_ARGS
        cmd = f'vlc {extra_args} {title_arg} "{video.url}"'
        self.shell_execute(cmd)


class CVLCPlayer(VLCPlayer):
    PLAYER = "cvlc"


class FFMPEGRouter(BasePlayer):
    """ffmpeg router for redirect video bytes to player by shell pipe `|`

    useful, if player not support http headers arguments
    """

    LOGLEVEL_ARG = "-loglevel error"

    URL_ARG = '-i "{}"'
    HLS_ARGS = (
        "-c copy -f hls -hls_flags append_list+omit_endlist -hls_segment_type mpegts -hls_playlist_type vod pipe:1"
    )
    PLAYER_ARG = "| {} {} -"
    HEARERS_ARG = "-headers "

    def play_from_playlist(
        self, videos: List["Video"], names: List[str], headers: Optional[Dict] = None, quality: int = 1080
    ):
        msg = "Not supported m3u playlist"
        raise NotImplementedError(msg)

    @classmethod
    def _headers(cls, headers: dict):
        if headers:
            arg = f'{cls.HEARERS_ARG}"'
            for k, v in headers.items():
                arg += f"{k}: {v}\n"
            return f'{arg}" '
        return ""

    def play(self, video: "Video", title: Optional[str] = None, player: Optional[str] = None, **kwargs):  # noqa
        title_arg = ""
        headers_arg = self._headers(video.headers)
        url = self.URL_ARG.format(video.url)
        title_arg = title_arg.format(title) if title_arg and title else ""

        cmd = (
            f"ffmpeg "
            f"{self.LOGLEVEL_ARG} {headers_arg} {url} {self.HLS_ARGS} {self.PLAYER_ARG.format(player, title_arg)}"
        )
        subprocess.Popen(cmd, shell=True).wait()


def run_video(video: "Video", app_cfg: "Config", title: Optional[str] = None):
    if app_cfg.USE_FFMPEG_ROUTE:
        if app_cfg.PLAYER == "mpv":
            FFMPEGRouter(app_cfg).play(video, title, player=app_cfg.PLAYER, title_arg='--title="{}"')
        elif app_cfg.PLAYER in ("vlc", "cvlc"):
            FFMPEGRouter(app_cfg).play(video, title, player=app_cfg.PLAYER, title_arg='--meta-title "{}"')
        return
    elif app_cfg.PLAYER == "mpv":
        return MpvPlayer(app_cfg).play(video, title)
    elif app_cfg.PLAYER == "vlc":
        return VLCPlayer(app_cfg).play(video, title)


def run_m3u_playlist(videos: List["Video"], names: List[str], app_cfg: "Config"):
    MpvPlayer(app_cfg).play_from_playlist(videos, names, quality=app_cfg.MIN_QUALITY)
