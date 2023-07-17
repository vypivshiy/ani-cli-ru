from eggella import Eggella

from anicli_api.source import animego

app = Eggella("anicli")


EXTRACTOR = animego.Extractor()
PLAYER = "mpv"
# TODO add vlc and implement simple proxy server for redirects