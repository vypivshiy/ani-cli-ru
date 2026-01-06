import asyncio
import subprocess
from importlib.metadata import version as pkg_version
from typing import Optional, TypedDict

import httpx


CMD_PIPX_UNINSTALL = "pipx uninstall anicli-ru"
CMD_PIPX_INSTALL = "pipx install anicli-ru"
CMD_PIPX_UPGRADE_FORCE = "pipx upgrade --force {}"
CMD_PIPX_UPGRADE = "pipx upgrade {}"
CMD_PIPX_UPGRADE_PIP_PKG = "pipx runpip {} install --upgrade --force-reinstall {}"
CMD_PIPX_INSTALL_UPGRADE = "pipx runpip {} install {} -U"

CMD_UV_UNINSTALL = "uv tool uninstall anicli-ru"
CMD_UV_INSTALL = "uv tool install anicli-ru"
CMD_UV_UPGRADE_REINSTALL = "uv tool upgrade {} --reinstall"
CMD_UV_UPGRADE = "uv tool upgrade {}"
CMD_UV_UPGRADE_PACKAGE = "uv tool upgrade {} --upgrade-package {}"


class UpdateExceptionError(Exception):
    pass


def get_api_version() -> str:
    return pkg_version("anicli-api")


def _check_installed_cli_package(cmd: str, cli_package: str = "anicli-ru") -> bool:
    """Check if a CLI package is installed using the given command."""
    try:
        proc = subprocess.run(cmd, check=False, shell=True, text=True, capture_output=True)
        return proc.returncode == 0 and cli_package in proc.stdout
    except Exception:
        return False


def is_installed_in_pipx() -> bool:
    """Check if anicli-ru is installed via pipx."""
    return _check_installed_cli_package("pipx list")


def is_installed_in_uv() -> bool:
    """Check if anicli-ru is installed via uv."""
    return _check_installed_cli_package("uv tool list")


def reinstall_pipx():
    """Completely reinstall anicli-ru using pipx."""
    try:
        subprocess.run(CMD_PIPX_UNINSTALL, shell=True, check=True)
        subprocess.run(CMD_PIPX_INSTALL, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        msg = "Error reinstalling via pipx"
        raise UpdateExceptionError(msg) from e


def reinstall_uv():
    """Completely reinstall anicli-ru using uv."""
    try:
        subprocess.run(CMD_UV_UNINSTALL, shell=True, check=True)
        subprocess.run(CMD_UV_INSTALL, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        msg = "Error reinstalling via uv"
        raise UpdateExceptionError(msg) from e


def update_pipx(package: str = "anicli-ru", dependency: str = "anicli-api", force: bool = False) -> bool:
    """
    Update a pipx-installed tool.

    Args:
        package: the pipx package/tool name (default "anicli-ru")
        dependency: a dependency inside the tool's venv to (optionally) update (default "anicli-api")
        force: if True -> force reinstall (uses --force / --force-reinstall); otherwise normal upgrade

    Returns:
        True on success

    Raises:
        UpdateExceptionError on failure
    """
    try:
        if force:
            # Force pipx to re-run installation (under the hood pip install --force-reinstall)
            subprocess.run(CMD_PIPX_UPGRADE_FORCE.format(package), shell=True, check=True)

            # Forcibly reinstall dependency inside the package venv
            subprocess.run(
                CMD_PIPX_UPGRADE_PIP_PKG.format(package, dependency),
                shell=True,
                check=True,
            )
            # repeat to be robust against pip cache/state (optional but mirrors prior behavior)
            subprocess.run(
                CMD_PIPX_UPGRADE_PIP_PKG.format(package, dependency),
                shell=True,
                check=True,
            )
        else:
            # Normal upgrade path
            subprocess.run(CMD_PIPX_UPGRADE.format(package), shell=True, check=True)

            # Update dependency inside the venv normally
            subprocess.run(
                CMD_PIPX_INSTALL_UPGRADE.format(package, dependency),
                shell=True,
                check=True,
            )
            subprocess.run(
                CMD_PIPX_INSTALL_UPGRADE.format(package, dependency),
                shell=True,
                check=True,
            )

        return True
    except subprocess.CalledProcessError as e:
        msg = f"Error {'force-' if force else ''}updating via pipx for package {package}"
        raise UpdateExceptionError(msg) from e


def update_uv(package: str = "anicli-ru", dependency: str = "anicli-api", force: bool = False) -> bool:
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
            # Try upgrade with reinstall (reinstalls packages in the tool environment)
            subprocess.run(CMD_UV_UPGRADE_REINSTALL.format(package), shell=True, check=True)

            # Reinstall/refresh specific dependency inside the tool environment.
            subprocess.run(
                CMD_UV_UPGRADE_PACKAGE.format(package, dependency),
                shell=True,
                check=True,
            )
            # repeat to be robust against caching/refresh timing (optional)
            subprocess.run(
                CMD_UV_UPGRADE_PACKAGE.format(package, dependency),
                shell=True,
                check=True,
            )

            # Fallback option (uncomment if you prefer overwrite install):
            # subprocess.run(f"uv tool install {package} --force", shell=True, check=True)
        else:
            # Normal upgrade
            
            subprocess.run(CMD_UV_UPGRADE.format(package), shell=True, check=True)

            # Normal dependency upgrade inside the tool environment
            subprocess.run(
                CMD_UV_UPGRADE_PACKAGE.format(package, dependency),
                shell=True,
                check=True,
            )
            subprocess.run(
                CMD_UV_UPGRADE_PACKAGE.format(package, dependency),
                shell=True,
                check=True,
            )

        return True
    except subprocess.CalledProcessError as e:
        msg = f"Error {'force-' if force else ''}updating via uv for package {package}"
        raise UpdateExceptionError(msg) from e


async def get_package_version_from_pypi(package_name: str, current_version: Optional[str] = None) -> "TPACKAGE":
    """
    Get the latest version information for a package from PyPI.

    Args:
        package_name: Name of the package to check
        current_version: Optional current version to compare against

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
                "is_outdated": current_version is not None and current_version != latest_version,
            }

            return result  # type: ignore
        except httpx.RequestError:
            raise
        except KeyError:
            raise ValueError(f"Unexpected response format from PyPI for {package_name}")


class TPACKAGE(TypedDict):
    package_name: str
    current_version: str
    latest_version: str
    is_outdated: bool


class TVERSION(TypedDict):
    anicli_ru: TPACKAGE
    anicli_api: TPACKAGE


async def check_for_updates(
    current_anicli_ru_version: Optional[str] = None, current_anicli_api_version: Optional[str] = None
) -> TVERSION:
    """
    Check for updates for both anicli-ru and anicli-api packages.

    Args:
        current_anicli_ru_version: Current version of anicli-ru
        current_anicli_api_version: Current version of anicli-api

    Returns:
        Dict containing update information for both packages
    """

    # Run both checks concurrently
    anicli_ru_task = get_package_version_from_pypi("anicli-ru", current_anicli_ru_version)
    anicli_api_task = get_package_version_from_pypi("anicli-api", current_anicli_api_version)

    results = await asyncio.gather(anicli_ru_task, anicli_api_task)

    return {"anicli_ru": results[0], "anicli_api": results[1]}
