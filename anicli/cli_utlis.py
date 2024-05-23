import subprocess


def is_command_available(command: str) -> bool:
    try:
        # Use subprocess to run the command with a dry run ("-n") option
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True  # The command is available
    except subprocess.CalledProcessError:
        return False  # The command is not available


def command_available(command: str) -> bool:
    proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode == 0


def is_ffmpeg_installed():
    return is_command_available("ffmpeg -version")
