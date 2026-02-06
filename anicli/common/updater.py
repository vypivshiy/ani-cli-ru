import asyncio
import subprocess
from importlib.metadata import version as pkg_version
from typing import List, TypedDict

import httpx
from typer import BadParameter

import anicli

# --- Constants & Types ---


class TPACKAGE(TypedDict):
    package_name: str
    current_version: str
    latest_version: str
    is_outdated: bool


class TVERSION(TypedDict):
    anicli_ru: TPACKAGE
    anicli_api: TPACKAGE


class UpdateExceptionError(Exception):
    pass


# --- Internal Helpers ---


def _run_cmd(args: List[str]) -> subprocess.CompletedProcess:
    """Safely run a system command without shell=True."""
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise UpdateExceptionError(f"Command failed: {' '.join(args)}") from e


def get_api_version() -> str:
    return pkg_version("anicli-api")


def _check_installed_cli_package(
    args: List[str], cli_package: str = "anicli-ru"
) -> bool:
    """Check if a CLI package is installed using the given command."""
    try:
        proc = _run_cmd(args)
        return proc.returncode == 0 and cli_package in proc.stdout
    except Exception:
        return False


def is_installed_in_pipx() -> bool:
    """Check if anicli-ru is installed via pipx."""
    return _check_installed_cli_package(["pipx", "list"])


def is_installed_in_uv() -> bool:
    """Check if anicli-ru is installed via uv."""
    return _check_installed_cli_package(["uv", "tool", "list"])


def update_pipx(
    package: str = "anicli-ru", dependency: str = "anicli-api", force: bool = False
) -> bool:
    """
    Update a pipx-installed tool.

    Args:
        package: the pipx package/tool name (default "anicli-ru")
        dependency: a dependency inside the tool's venv to (optionally) update (default "anicli-api")
        force: if True -> force reinstall (uses --force / --force-reinstall); otherwise normal upgrade

    Returns:
        True on success
    """
    try:
        if force:
            _run_cmd(["pipx", "upgrade", "--force", package])
            _run_cmd(
                [
                    "pipx",
                    "runpip",
                    package,
                    "install",
                    "--upgrade",
                    "--force-reinstall",
                    dependency,
                ]
            )
        else:
            _run_cmd(["pipx", "upgrade", package])
            _run_cmd(["pipx", "runpip", package, "install", "-U", dependency])
        return True
    except UpdateExceptionError:
        # Fallback to full reinstall if upgrade fails
        _run_cmd(["pipx", "uninstall", package])
        _run_cmd(["pipx", "install", package])
        return True


def update_uv(
    package: str = "anicli-ru", dependency: str = "anicli-api", force: bool = False
) -> bool:
    """
    Update a uv-managed tool.

    Args:
        package: the uv tool name (default "anicli-ru")
        dependency: a dependency in the tool environment to (optionally) update (default "anicli-api")
        force: if True -> attempt forced reinstall/refresh; otherwise normal upgrade

    Returns:
        True on success

    Raises:
        UpdateExceptionError on failure
    """
    try:
        if force:
            _run_cmd(["uv", "tool", "upgrade", package, "--reinstall"])
        else:
            _run_cmd(["uv", "tool", "upgrade", package])

        # In uv, we can target specific package upgrade in the tool environment
        _run_cmd(["uv", "tool", "upgrade", package, "--upgrade-package", dependency])
        return True
    except UpdateExceptionError:
        _run_cmd(["uv", "tool", "uninstall", package])
        _run_cmd(["uv", "tool", "install", package])
        return True


def update_tool(
    package: str = "anicli-ru", dependency: str = "anicli-api", force: bool = False
):
    is_pipx, is_uv = is_installed_in_pipx(), is_installed_in_uv()
    if not is_pipx and not is_uv:
        msg = "anicli-ru package not founded in pipx or uv tool"
        raise BadParameter(msg)
    if is_uv:
        update_uv(package, dependency, force=force)
    elif is_pipx:
        update_pipx(package, dependency, force=force)


async def get_package_version_from_pypi(
    package_name: str, current_version: str
) -> "TPACKAGE":
    """
    Get the latest version information for a package from PyPI.

    Args:
        package_name: Name of the package to check
        current_version: current version to compare against

    Returns:
        Dict containing version info, including 'current_version', 'latest_version', and 'is_outdated'
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"https://pypi.org/pypi/{package_name}/json")
            response.raise_for_status()

            data = response.json()
            latest_version = data["info"]["version"]

            result = {
                "package_name": package_name,
                "current_version": current_version,
                "latest_version": latest_version,
                "is_outdated": (
                    current_version != latest_version if current_version else False
                ),
            }

            return result  # type: ignore
        except (httpx.HTTPError, KeyError):
            # Return 'unknown' state instead of crashing the app
            return {
                "package_name": package_name,
                "current_version": current_version,
                "latest_version": "unknown",
                "is_outdated": False,
            }


async def check_for_updates() -> TVERSION:
    """
    Check for updates for both anicli-ru and anicli-api packages.

    Returns:
        Dict containing update information for both packages
    """

    # Run both checks concurrently
    tasks = [
        get_package_version_from_pypi("anicli-ru", anicli.__version__),
        get_package_version_from_pypi("anicli-api", get_api_version()),
    ]
    results = await asyncio.gather(*tasks)

    return {"anicli_ru": results[0], "anicli_api": results[1]}
