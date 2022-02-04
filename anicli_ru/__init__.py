from anicli_ru.loader import all_extractors, import_extractor
__version__ = "3.0.3"


def check_update():
    """check last version package"""
    import requests
    import re
    r = requests.get("https://raw.githubusercontent.com/vypivshiy/ani-cli-ru/master/anicli_ru/__init__.py")
    version, = re.findall(r'__version__ = "([\d.]+)"', r.text)
    return version


if __name__ == '__main__':
    print(check_update())
