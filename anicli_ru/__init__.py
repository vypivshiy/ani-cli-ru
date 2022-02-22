from anicli_ru.loader import all_extractors, import_extractor


def check_update(package_name: str) -> str:
    """return last version from pypi package"""
    import requests
    r = requests.get(f"https://pypi.org/pypi/{package_name}/json/").json()
    version = list(r["releases"].keys())[-1]
    return version
