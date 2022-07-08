"""defaults values for project"""
import re
from typing import Pattern, NamedTuple

from anicli_ru.utils import BasePatternModel, RegexField

# outdated signatures for kodik
# RE_URL = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
# RE_URL_DATA = re.compile(r'iframe.src = "//(.*?)"')
# RE_VIDEO_TYPE = re.compile(r"go/(\w+)/\d+")
# RE_VIDEO_ID = re.compile(r"go/\w+/(\d+)")
# RE_VIDEO_HASH = re.compile(r"go/\w+/\d+/(.*?)/\d+p\?")


# Kodik
class KodikPatterns(BasePatternModel):
    d = RegexField(str, re.compile(r'"d":"(.*?)"'))
    d_sign = RegexField(str, re.compile(r'"pd":"(.*?)"'))
    pd_sign = RegexField(str, re.compile(r'"pd_sign":"(.*?)"'))
    ref = RegexField(str, re.compile(r'"ref":"(.*?)"'))
    ref_sign = RegexField(str, re.compile(r'"ref_sign":"(.*?)"'))
    hash = RegexField(str, re.compile(r"videoInfo\.hash = '(\w+)';"))
    id = RegexField(str, re.compile(r'var videoId = "(\d+)"'))
    bad_user: bool = True
    info: str = "{}"
    QUALITY = (720, 480, 360)
    KODIK_URL_VALIDATE = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
    REFERER = "https://kodik.info"


# Aniboom
class AniboomPatterns(BasePatternModel):
    RE_M3U8 = re.compile(r'"hls":"{\\"src\\":\\"(.*\.m3u8)\\"')
    RE_MPD = re.compile(r'"{\\"src\\":\\"(.*\.mpd)\\"')
    # parse master.m3u8, return [(quality, url), ...] results
    RE_M3U8_DATA = re.compile(r'''#EXT\-X\-STREAM\-INF\:BANDWIDTH=\d+,RESOLUTION=(\d+x\d+),CODECS=".*?",AUDIO=".*?" {4}(.*?\.m3u8)''')
    QUALITY = (1080, 720, 480, 360)  # works only m3u8 format
    REFERER = "https://aniboom.one"
    USERAGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, " \
                "like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36 "
    ACCEPT_LANG = "ru-RU"


# Aniboom M3U8 object
class AniboomM3U8Data(NamedTuple):
    quality: str
    url_suffix: str


# check response headers "Server" key
DDOS_SERVICES = ("cloudflare", "ddos-guard")