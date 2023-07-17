from typing import TYPE_CHECKING, Any, Optional, Iterable, List
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
    def play_many(cls, videos: List["Video"], titles: Optional[List[str]] = None):
        if not titles:
            headers_arg = cls._parse_headers_args(videos[0].headers)
            videos_arg = " ".join(v.url for v in videos)
            subprocess.Popen(f"{cls.PLAYER} {headers_arg} {videos_arg}", shell=True).wait()
        else:
            headers_arg = cls._parse_headers_args(videos[0].headers)
            videos_arg = " ".join(
                f'{cls.TITLE.format(title)} "{video.url}"'
                for video, title in zip(videos, titles)
            )
            subprocess.Popen(f"{cls.PLAYER} {headers_arg} {videos_arg}")
