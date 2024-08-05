import os
import subprocess
import tempfile
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Optional, List

from anicli_api.tools import generate_playlist

if TYPE_CHECKING:
    from anicli_api.base import Video


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
        return f'"{arg}"'

    @staticmethod
    def shell_execute(cmd: str):
        print("Executing: %s", cmd)
        if os.name == "nt":
            proc = subprocess.Popen(cmd)
        else:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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


def run_video(video: "Video", title: Optional[str] = None):
    return MpvPlayer.play(video, title)


def run_m3u_playlist(videos: List["Video"], names: List[str], quality: int = 1080):
    MpvPlayer.play_from_playlist(videos, names, quality=quality)
