from urllib.parse import urlsplit

from anicli_api.base import HTTPSync

from anicli.check_updates import check_version
from anicli.cli.config import app


@app.on_startup()
def setup_http_config():
    app.CFG.EXTRACTOR.http = HTTPSync(proxy=app.CFG.PROXY, timeout=app.CFG.TIMEOUT)
    # todo video extractor provide config


@app.on_startup()
def loaded_extractor_msg():
    app.cmd.print_ft("Loaded source provider:", urlsplit(app.CFG.EXTRACTOR.BASE_URL).netloc)

@app.on_startup()
def check_updates():
    result_api, current_api, new_api = check_version()
    result_client, current_client, new_client = check_version("anicli-ru")
    if result_api:
        print(f"available new anicli-api version: (current: {current_api}, new: {new_api})")
    elif result_client:
        print(f"available new anicli-ru version: (current: {current_api}, new: {new_api})")
    if result_api or result_client:
        print("close app and run `anicli-ru -U` to get updates")
