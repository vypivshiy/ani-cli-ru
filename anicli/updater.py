import subprocess

def _check_installed_cli_package(cmd: str, cli_package: str="anicli-ru") -> bool:
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode == 0 and cli_package in proc.stdout

def is_installed_in_pipx() -> bool:
    return _check_installed_cli_package("pipx list")

def is_installed_in_uv():
    return _check_installed_cli_package("uv tool list")


def update_pipx():
    # double calls:
    # first - update pypi cache, second - update package
    subprocess.run("pipx runpip anicli-ru install anicli-api -U", shell=True, stdout=subprocess.PIPE)
    subprocess.run("pipx runpip anicli-ru install anicli-api -U", shell=True)

def update_uv():
    subprocess.run("uv tool upgrade anicli-ru", shell=True)
