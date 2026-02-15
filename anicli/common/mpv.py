import shutil
import tempfile
from asyncio.subprocess import Process, create_subprocess_exec  # noqa
from pathlib import Path
from typing import Dict, List, Sequence

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


def _build_mpv_args(headers: Dict[str, str]) -> List[str]:
    """Build shared mpv arguments for headers and extra options."""
    args = []

    user_agent = headers.get("User-Agent") or headers.get("user-agent")
    referer = headers.get("Referer") or headers.get("referer")

    if user_agent:
        args.append(f"{USER_AGENT_KEY}={user_agent}")
    if referer:
        args.append(f"{REFERER_KEY}={referer}")

    # All other headers go to --http-header-fields
    others = [
        f"{k}: {v}"
        for k, v in headers.items()
        if k.lower() not in ("user-agent", "referer")
    ]
    if others:
        args.append(f"{HEADERS_KEY}={','.join(others)}")

    return args


async def _run_player(args: List[str]):
    # Execute player process without shell invocation for safety
    print(f"Executing: {PLAYER} {' '.join(args)}")
    process = await create_subprocess_exec(PLAYER, *args)
    await process.wait()


async def play_mpv_video(video: Video, title: str, mpv_opts: str = "") -> None:
    """Play a single video."""
    title = sanitize_filename(title)

    args = [f"{TITLE_KEY}={title}"]
    if video.headers:
        args.extend(_build_mpv_args(video.headers))
    if mpv_opts:
        args.extend(mpv_opts.split())

    args.append(video.url)
    await _run_player(args)


async def play_mpv_batched_videos(
    videos: Sequence[Video], titles: Sequence[str], mpv_opts: str = ""
) -> None:
    """generate playlist file in tempdir and execute to mpv via shell"""
    args = []

    # all videos same equal provider
    # eg: only aniboom, jutsu, or sibnet
    headers = videos[0].headers
    if headers:
        args.extend(_build_mpv_args(headers))
    if mpv_opts:
        args.extend(mpv_opts.split())

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".m3u", encoding="utf-8"
    ) as temp_file:
        raw_playlist = generate_m3u_str_playlist(videos, titles)
        temp_file.write(raw_playlist)
        playlist_path = temp_file.name
    try:
        args.append(playlist_path)
        await _run_player(args)
    finally:
        # Ensure cleanup of the temporary file after player exit
        p = Path(playlist_path)
        if p.exists():
            p.unlink()
