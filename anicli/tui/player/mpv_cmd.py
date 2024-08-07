import subprocess
import tempfile
from contextlib import contextmanager
from tempfile import _TemporaryFileWrapper  # type: ignore

from anicli.tui.player.sanitize import sanitize_filename

# remind: powershell only support strings with '"' quotes

PLAYER_EXE = "mpv"
TITLE = "--title"
HEADERS_KEY = "--http-header-fields"
USER_AGENT_KEY = "--user-agent"


def sanitize_title(title: str) -> str:
    return sanitize_filename(title)


def build_headers_args(headers: dict[str, str]) -> list[str]:
    if not headers:
        return []
    # multiple command key build List Options:
    # shlex don't support mpv list arguments feature
    # Note:
    #       don't need whitespace see: man mpv, \http-header-fields
    #                                 v
    # --http-header-fields="Spam: egg","Foo: bar","BAZ: ZAZ"
    user_agent_arg = ''
    headers_option = ''
    headers_args = []

    for k, v in headers.items():
        if k.lower() == 'user-agent':
            user_agent_arg = f'{USER_AGENT_KEY}="{v}"'
            continue
        headers_args.append(f'"{k}: {v}"')

    if headers_args:
        headers_option = f'{USER_AGENT_KEY}=' + ','.join(headers_args)

    if user_agent_arg and headers_args:
        return [user_agent_arg, headers_option]
    elif headers_args:
        return [headers_option]
    elif user_agent_arg:
        return [user_agent_arg]


def build_title_args(title: str) -> list[str]:
    if not title:
        return []

    return [f'{TITLE}="{sanitize_title(title)}"']


@contextmanager
def new_tmp_playlist(playlist_raw: str) -> str:
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.m3u') as temp_file:
        temp_file.write(playlist_raw)
    try:
        yield temp_file.name
    finally:
        temp_file.close()


def run_playlist(playlist_raw: str, headers: dict[str, str]) -> None:
    with new_tmp_playlist(playlist_raw) as pl_path:
        args = [PLAYER_EXE,
                f'"{pl_path}"',
                ] + build_headers_args(headers)
        cmd = ' '.join(args)
        # TODO: redirect log to app
        pid = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pid.wait()
