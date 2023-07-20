from anicli.cli.config import app
from urllib.parse import urlsplit


@app.on_startup()
def loaded_extractor_msg():
    app.cmd.print_ft("Loaded source provider:", urlsplit(app.CFG.EXTRACTOR.BASE_URL).netloc)
