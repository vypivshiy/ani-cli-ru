from urllib.parse import quote_plus

from typing import TYPE_CHECKING, Any, Optional, List
import subprocess

if TYPE_CHECKING:
    from anicli_api.player.base import Video


class MpvPlayer:
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
    def play(cls, video: "Video", title: Optional[str] = None):
        title_arg = cls.TITLE.format(title) if title else ""
        headers_arg = cls._parse_headers_args(video.headers)
        subprocess.Popen(f'{cls.PLAYER} {title_arg} {headers_arg} "{video.url}"', shell=True).wait()

    @classmethod
    def play_from_redirect_server(cls, video: "Video", title: Optional[str] = None):
        title_arg = cls.TITLE.format(title) if title else ""
        # TODO customisation ip and port
        server_argument = f"http://127.0.0.1:10007?" \
                          f"url={quote_plus(video.url)}&headers={quote_plus(str(video.headers))}"
        print("Past this url to videoplayer if you have any troubles:", "\n\t", server_argument)
        subprocess.Popen(f'{cls.PLAYER} {title_arg} "{server_argument}"', shell=True).wait()


class FFMPEGRouter:
    """ffmpeg router for redirect video to players

    useful, if player not support http headers arguments
    """
    LOGLEVEL_ARG = "-loglevel error"
    URL_ARG = '-i "{}"'
    HLS_ARGS = "-c copy -f hls -hls_flags append_list+omit_endlist " \
                      "-hls_segment_type mpegts -hls_playlist_type vod pipe:1"
    PLAYER_ARG = "| {} -"
    HEARERS_ARG = "-headers "

    @classmethod
    def _headers(cls, headers: dict):
        arg = cls.HEARERS_ARG
        if headers:
            for k, v in headers.items():
                arg += f'{k}: {v}\n'
            return f'"{arg}"'
        return ""

    @classmethod
    def play(cls, video: "Video", player_name: str):
        headers_arg = cls._headers(video.headers)
        url = cls.URL_ARG.format(video.url)
        cmd = f'ffmpeg {cls.LOGLEVEL_ARG} {headers_arg} {url} {cls.HLS_ARGS} {cls.PLAYER_ARG.format(player_name)}'
