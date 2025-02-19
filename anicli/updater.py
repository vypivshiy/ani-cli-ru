import subprocess


def _check_installed_cli_package(cmd: str, cli_package: str="anicli-ru") -> bool:
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode == 0 and cli_package in proc.stdout


def is_installed_in_pipx() -> bool:
    return _check_installed_cli_package("pipx list")


def is_installed_in_uv():
    return _check_installed_cli_package("uv tool list")


def update_pipx():
    subprocess.run("pipx upgrade anicli-ru -q", shell=True)

    # double calls required for update pip cache and guaranteed get actual version
    subprocess.run("pipx runpip anicli-ru install anicli-api -U -q", shell=True)
    subprocess.run("pipx runpip anicli-ru install anicli-api -U -q", shell=True)


def update_uv():
    subprocess.run("uv tool upgrade anicli-ru -q", shell=True)

    subprocess.run("uv tool upgrade anicli-ru --upgrade-package anicli-api -q", shell=True)
    subprocess.run("uv tool upgrade anicli-ru --upgrade-package anicli-api -q", shell=True)
