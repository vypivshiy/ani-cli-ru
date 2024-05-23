import subprocess


def command_available(command: str) -> bool:
    proc = subprocess.run(  # noqa
        command,
        shell=True,  # noqa
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False)
    return proc.returncode == 0


def is_ffmpeg_installed():
    return command_available("ffmpeg -version")
