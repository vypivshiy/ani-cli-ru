import asyncio
import contextlib
import json
import os
import platform
import shlex
import shutil
import tempfile
from asyncio.subprocess import Process, create_subprocess_exec  # noqa
from pathlib import Path
from typing import Dict, List, Sequence, Union

from anicli_api.player.base import Video

from anicli.common.config import AppManager
from anicli.common.m3u import generate_m3u_str_playlist
from anicli.common.sanitizer import sanitize_filename

PLAYER = "mpv"
TITLE_KEY = "--title"
HEADERS_KEY = "--http-header-fields"
USER_AGENT_KEY = "--user-agent"
REFERER_KEY = "--referrer"


class MpvIpc:
    def __init__(self):
        self.tmp_dir = None
        self.socket_path = None

    def __enter__(self):
        if platform.system() == "Windows":
            self.socket_path = rf"\\.\pipe\mpvserver_{os.getpid()}"
        else:
            self.tmp_dir = Path(tempfile.mkdtemp(prefix="anicli_mpv_"))
            self.socket_path = str(self.tmp_dir / "socket")
        return self.socket_path

    def __exit__(self, exc_type, exc, tb):
        if self.tmp_dir and self.tmp_dir.exists():
            for p in self.tmp_dir.iterdir():
                p.unlink()
            self.tmp_dir.rmdir()

# TODO:
# class MPVController:
#     def init(
#         self, video: Union[Video, Sequence[Video]], title: Union[str, Sequence[str]]
#     ):
#         self.video = video
#         self.title = title

#     async def play(self, mpv_opts: str = ""):
#         if self.video:
#             ...

#     async def pause(): ...

#     async def seek(sec): ...

#     async def observe_time(): ...

#     async def quit(): ...


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


async def _run_player(args: List[str], ipc_socket: str):
    # Execute player process without shell invocation for safety
    print(f"Executing: {PLAYER} {' '.join(args)}")
    process = await create_subprocess_exec(PLAYER, *args)

    if platform.system() != "Windows":
        for _ in range(50):
            if Path(ipc_socket).exists():
                break
            await asyncio.sleep(0.1)

    monitor_task = asyncio.create_task(monitor_time(process, ipc_socket))

    try:
        await process.wait()
    finally:
        monitor_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await monitor_task


async def play_mpv_video(video: Video, title: str, mpv_opts: str = "") -> None:
    """Play a single video."""
    with MpvIpc() as ipc:
        title = sanitize_filename(title)

        args = [f"{TITLE_KEY}={title}"]

        if video.headers:
            args.extend(_build_mpv_args(video.headers))
        if mpv_opts:
            args.extend(shlex.split(mpv_opts))
        args.append(f"--input-ipc-server={ipc}")
        args.append(video.url)

        await _run_player(args, ipc)


async def play_mpv_batched_videos(
    videos: Sequence[Video], titles: Sequence[str], mpv_opts: str = ""
) -> None:
    """generate playlist file in tempdir and execute to mpv via shell"""
    with MpvIpc() as ipc:
        args = []

        # all videos same equal provider
        # eg: only aniboom, jutsu, or sibnet
        headers = videos[0].headers
        if headers:
            args.extend(_build_mpv_args(headers))
        if mpv_opts:
            args.extend(shlex.split(mpv_opts))

        args.append(f"--input-ipc-server={ipc}")

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".m3u", encoding="utf-8"
        ) as temp_file:
            raw_playlist = generate_m3u_str_playlist(videos, titles)
            temp_file.write(raw_playlist)
            playlist_path = temp_file.name
        try:
            args.append(playlist_path)
            await _run_player(args, ipc)
        finally:
            # Ensure cleanup of the temporary file after player exit
            p = Path(playlist_path)
            if p.exists():
                p.unlink()


def _windows_ipc_request(pipe_path: str, command: dict):
    try:
        with open(pipe_path, "w+b", buffering=0) as f:
            f.write(json.dumps(command).encode() + b"\n")
            f.flush()
            line = f.readline()
            return json.loads(line.decode()) if line else None
    except Exception:
        return None


async def get_mpv_property(property_name: str, ipc_socket: str):
    """Get property from MPV IPC"""
    command = {"command": ["get_property", property_name]}
    if platform.system() == "Windows":
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, _windows_ipc_request, ipc_socket, command
        )
    else:
        reader, writer = await asyncio.open_connection(ipc_socket)

        writer.write(json.dumps(command).encode() + b"\n")
        await writer.drain()
        line = await reader.readline()
        writer.close()
        await writer.wait_closed()

        response = json.loads(line.decode())

    if response and response.get("error") == "success":
        return response.get("data")
    return None


async def monitor_time(
    process: asyncio.subprocess.Process, ipc_socket: str, interval: int = 10
):
    """Monitoring time from mpv player in background"""
    last_time = None
    while True:
        if process.returncode is not None:
            break
        await asyncio.sleep(interval)
        try:
            time_pos = await get_mpv_property("time-pos", ipc_socket)
            if time_pos is not None:
                try:
                    time_pos = int(time_pos)
                except (TypeError, ValueError):
                    continue
                if time_pos != last_time:
                    last_time = time_pos
                    AppManager.edit_last_history("time", last_time)
        except Exception:
            await asyncio.sleep(1)
