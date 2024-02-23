import logging
from urllib.parse import urlsplit

from anicli_api.base import HTTPSync

from anicli.cli.config import app


@app.on_startup()
def setup_http_config():
    if app.CFG.PROXY:
        app.cmd.print_ft("Setup proxy")
    if app.CFG.TIMEOUT:
        app.cmd.print_ft("Setup timeout")
    HTTPSync(**app.CFG.httpx_kwargs())


@app.on_startup()
def loaded_extractor_msg():
    app.cmd.print_ft("Loaded source provider:", urlsplit(app.CFG.EXTRACTOR.BASE_URL).netloc)
