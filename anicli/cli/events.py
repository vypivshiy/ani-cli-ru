from urllib.parse import urlsplit

from anicli_api.base import HTTPSync

from anicli.check_updates import check_version
from anicli.cli.config import app


@app.on_startup()
def setup_http_config():
    if app.CFG.PROXY:
        app.cmd.print_ft("Setup proxy")
    if app.CFG.TIMEOUT:
        app.cmd.print_ft("Setup timeout")
    app.CFG.EXTRACTOR.http = HTTPSync(proxies=app.CFG.PROXY, timeout=app.CFG.TIMEOUT)
    # todo video extractor provide config


@app.on_startup()
def loaded_extractor_msg():
    app.cmd.print_ft("Loaded source provider:", urlsplit(app.CFG.EXTRACTOR.BASE_URL).netloc)

@app.on_startup()
def check_anicli_api_version():
    result, current, new = check_version()
    if result:
        print()
        print(f"available new anicli-api version: (current: {current}, new: {new})")
        print("close app and run `anicli-ru --update` to update anicli-api package")
