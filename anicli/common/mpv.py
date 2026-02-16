import asyncio
import contextlib
import json
import os
import platform
import shlex
import shutil
import tempfile
from asyncio.streams import StreamReader, StreamWriter, open_connection
from asyncio.subprocess import create_subprocess_exec
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence

from anicli.common import history
from anicli.common.m3u import generate_m3u_str_playlist
from anicli.common.sanitizer import sanitize_filename

if TYPE_CHECKING:
    from anicli_api.player.base import Video

PLAYER = "mpv"
TITLE_KEY = "--title"
HEADERS_KEY = "--http-header-fields"
USER_AGENT_KEY = "--user-agent"
REFERER_KEY = "--referrer"


def is_mpv_installed() -> bool:
    return shutil.which("mpv") is not None


class MpvIpcClient:
    def __init__(self):
        self.tmp_dir: Optional[Path] = None
        self.socket_path: Optional[str] = None

        self.reader: Optional[StreamReader] = None
        self.writer: Optional[StreamWriter] = None

    async def __aenter__(self):
        if platform.system() == "Windows":
            self.socket_path = rf"\\.\pipe\mpvserver_{os.getpid()}"
        else:
            self.tmp_dir = Path(tempfile.mkdtemp(prefix="anicli_mpv_"))
            self.socket_path = str(self.tmp_dir / "socket")
            await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
            self.reader = None
        if self.tmp_dir and self.tmp_dir.exists():
            for p in self.tmp_dir.iterdir():
                p.unlink()
            self.tmp_dir.rmdir()

    async def connect(self) -> None:
        if self.reader:
            self.reader, self.writer = await open_connection(self.socket_path)

    async def send(self, command: dict):
        line = None
        if platform.system() == "Windows":
            loop = asyncio.get_running_loop()
            line = await loop.run_in_executor(None, self._windows_send, command)
        if self.reader and self.writer:
            self.writer.write(json.dumps(command).encode() + b"\n")
            await self.writer.drain()
            line = await self.reader.readline()

        if line:
            return json.loads(line.decode())

    async def read(self):
        line = None
        if platform.system() == "Windows":
            loop = asyncio.get_running_loop()
            line = await loop.run_in_executor(None, self._windows_read)
        if self.reader:
            line = await self.reader.readline()

        if line:
            return json.loads(line.decode())

    def _windows_read(self):
        try:
            if self.socket_path:
                with open(self.socket_path, "r+b", buffering=0) as f:
                    return f.readline()
        except Exception:
            return None

    def _windows_send(self, command: dict):
        try:
            if self.socket_path:
                with open(self.socket_path, "w+b", buffering=0) as f:
                    f.write(json.dumps(command).encode() + b"\n")
                    f.flush()
                    return f.readline()
        except Exception:
            return None


class MPVController:
    def __init__(
        self,
        videos: Sequence["Video"],
        titles: Sequence[str],
        *,
        mpv_opts: str = "",
        save_time: bool = False,
    ):
        self.videos = videos
        self.titles = titles
        self.mpv_opts = mpv_opts
        self.save_time = save_time

        self.ipc: Optional[MpvIpcClient] = None
        self.ipc_socket: Optional[str] = None

    async def play(self):
        async with MpvIpcClient() as ipc:
            self.ipc = ipc
            if self.ipc.socket_path:
                self.ipc_socket = self.ipc.socket_path

            args = []
            first_vid = self.videos[0]

            # all videos same equal provider
            # eg: only aniboom, jutsu, or sibnet
            headers = first_vid.headers
            if headers:
                args.extend(self._build_args(headers))
            if self.mpv_opts:
                args.extend(shlex.split(self.mpv_opts))

            args.append(f"--input-ipc-server={self.ipc_socket}")

            if len(self.videos) == 1:
                title = sanitize_filename(self.titles[0])
                args.extend([f"{TITLE_KEY}={title}", first_vid.url])
                await self._run_player(args)
                return

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".m3u", encoding="utf-8"
            ) as temp_file:
                raw_playlist = generate_m3u_str_playlist(self.videos, self.titles)
                temp_file.write(raw_playlist)
                playlist_path = temp_file.name
                args.append(playlist_path)
            try:
                await self._run_player(args)
            finally:
                # Ensure cleanup of the temporary file after player exit
                p = Path(playlist_path)
                if p.exists():
                    p.unlink()

    async def _monitor_time(self, interval: int = 10):
        if self.ipc:
            last_title = None
            last_time = None
            while True:
                try:
                    # title handler
                    title = await self.get_title()
                    if title != last_title:
                        last_title = title
                        history.update_last({"episode": title})

                    # time handler
                    if self.ipc:
                        time_resp = await self.ipc.send(
                            {"command": ["get_property", "time-pos"]}
                        )
                        if time_resp:
                            try:
                                t = int(time_resp.get("data"))
                                if t != last_time:
                                    last_time = t
                                    history.update_last({"time": t})
                            except (TypeError, ValueError):
                                pass
                    await asyncio.sleep(interval)
                except Exception as e:
                    print(e)
                    await asyncio.sleep(1)

    async def get_title(self):
        if self.ipc:
            response = await self.ipc.send({"command": ["get_property", "media-title"]})
            if response:
                return response.get("data")

    async def pause(self):
        if self.ipc:
            await self.ipc.send({"command": ["set_property", "pause", True]})

    async def seek(self, seconds: int):
        if self.ipc:
            await self.ipc.send({"command": ["seek", seconds, "absolute"]})

    async def quit(self):
        if self.ipc:
            await self.ipc.send({"command": ["quit"]})

    async def _run_player(self, args: List[str]):
        if self.ipc_socket:
            print(f"Executing: {PLAYER} {' '.join(args)}")
            process = await create_subprocess_exec(PLAYER, *args)

            if self.save_time:
                if platform.system() != "Windows":
                    for _ in range(50):
                        if Path(self.ipc_socket).exists():
                            break
                        await asyncio.sleep(0.1)
                monitor_task = asyncio.create_task(self._monitor_time())

                try:
                    await process.wait()
                finally:
                    monitor_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await monitor_task

            await process.wait()

    def _build_args(self, headers: Dict[str, str]) -> List[str]:
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
