import logging

from anicli.cli.config import app
from urllib.parse import urlsplit
from anicli_api._http import HTTPSync


@app.on_startup()
def setup_http_config():
    if app.CFG.PROXY:
        app.cmd.print_ft("Setup proxy")
    if app.CFG.TIMEOUT:
        app.cmd.print_ft("Setup timeout")
    HTTPSync(**app.CFG.httpx_kwargs())


@app.on_startup()
def sc_schema_set_logging():
    logging.getLogger("scrape_schema").setLevel(logging.ERROR)


@app.on_startup()
def loaded_extractor_msg():
    app.cmd.print_ft("Loaded source provider:", urlsplit(app.CFG.EXTRACTOR.BASE_URL).netloc)
