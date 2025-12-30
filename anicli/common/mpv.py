from asyncio.subprocess import create_subprocess_shell, Process  # noqa
from typing import Callable, Sequence, List, Dict
import tempfile
import shutil

from anicli_api.base import BaseAnime, BaseEpisode, BaseSource
from anicli_api.player.base import Video

from anicli.common.m3u import generate_m3u_str_playlist
from anicli.common.sanitizer import sanitize_filename

PLAYER = "mpv"
TITLE_KEY = "--title"
HEADERS_KEY = "--http-header-fields"
USER_AGENT_KEY = "--user-agent"
REFERER_KEY = "--referrer"


def is_mpv_installed() -> bool:
    return shutil.which("mpv") is not None


def _escape_shell_arg(arg: str) -> str:
    """Escape argument for shell execution, especially for Windows."""
    # For Windows compatibility, use double quotes and escape any quotes within
    if '"' in arg:
        arg = arg.replace('"', '\\"')
    if "'" in arg:
        arg = arg.replace("'", "\\'")
    return f'"{arg}"'


def _parse_other_headers(cmd_parts: List[str], headers: Dict[str, str]) -> None:
    other_headers = {k: v for k, v in headers.items() if k.lower() not in ["user-agent", "referer"]}
    if other_headers:
        headers_parts = []
        for k, v in other_headers.items():
            escaped_k = k.replace('"', '""')
            escaped_v = v.replace('"', '""')
            header_part = f"{escaped_k}: {escaped_v}"
            headers_parts.append(_escape_shell_arg(header_part))
        headers_str = ",".join(headers_parts)
        cmd_parts.append(f"{HEADERS_KEY}={headers_str}")


def _parse_referrer_header(cmd_parts: List[str], headers: Dict[str, str]) -> None:
    referer = headers.get("Referer") or headers.get("referer")
    if referer:
        cmd_parts.append(f"{REFERER_KEY}={_escape_shell_arg(referer)}")


def _parse_mpv_useragent_header(cmd_parts: List[str], headers: Dict[str, str]) -> None:
    user_agent = headers.get("User-Agent") or headers.get("user-agent")
    if user_agent:
        cmd_parts.append(f"{USER_AGENT_KEY}={_escape_shell_arg(user_agent)}")


# FIXME: wrap to quotas "" arguments
async def play_mpv_video(video: Video, title: str, mpv_opts: str = "") -> None:
    """
    Play a video using mpv

    Args:
        video: Video object
        title: title for video
        mpv_opts: extra raw mpv_opts (eg: profile for config) and add "as it"

    Returns:
        executed process
    """
    cmd_parts = [PLAYER]

    title = sanitize_filename(title)
    cmd_parts.append(f"{TITLE_KEY}={_escape_shell_arg(title)}")
    headers = video.headers
    if headers:
        _parse_mpv_useragent_header(cmd_parts, headers)
        _parse_referrer_header(cmd_parts, headers)
        _parse_other_headers(cmd_parts, headers)

    if mpv_opts:
        cmd_parts.append(mpv_opts)

    cmd_parts.append(_escape_shell_arg(video.url))
    full_cmd = " ".join(cmd_parts)

    print("Execute:", full_cmd)
    process = await create_subprocess_shell(full_cmd, shell=True)
    await process.wait()


async def play_mpv_batched_videos(videos: Sequence[Video], titles: Sequence[str], mpv_opts: str = "") -> None:
    """generate playlist file in tempdir and execute to mpv via shell"""
    cmd_parts = [PLAYER]
    cmd_parts = [PLAYER]

    # all videos same equal provider
    # eg: only aniboom, jutsu, or sibnet
    headers = videos[0].headers
    if headers:
        _parse_mpv_useragent_header(cmd_parts, headers)
        _parse_referrer_header(cmd_parts, headers)
        _parse_other_headers(cmd_parts, headers)

    if mpv_opts:
        cmd_parts.append(mpv_opts)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".m3u") as temp_file:
        raw_playlist = generate_m3u_str_playlist(videos, titles)
        temp_file.write(raw_playlist)
    try:
        cmd_parts.append(_escape_shell_arg(temp_file.name))
        full_cmd = " ".join(cmd_parts)

        print("Execute:", full_cmd)
        process = await create_subprocess_shell(full_cmd, shell=True)
        await process.wait()
    finally:
        temp_file.close()
