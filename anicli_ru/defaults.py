"""Default constants for this project"""
import re

# antiddos services strings detect
from typing import NamedTuple

DDOS_SERVICES = ("cloudflare", "ddos-guard")

# default user-agent for all project
USER_AGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, " \
             "like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36 "

BASE_HEADERS_DICT = {"user-agent": USER_AGENT,
                     "x-requested-with": "XMLHttpRequest"}


# outdated signatures for kodik
# RE_URL = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
# RE_URL_DATA = re.compile(r'iframe.src = "//(.*?)"')
# RE_VIDEO_TYPE = re.compile(r"go/(\w+)/\d+")
# RE_VIDEO_ID = re.compile(r"go/\w+/(\d+)")
# RE_VIDEO_HASH = re.compile(r"go/\w+/\d+/(.*?)/\d+p\?")

# kodik.info http request headers 12.07.22
# :method: POST
# :path: /gvi
# accept: application/json, text/javascript, */*; q=0.01
# accept-encoding: gzip, deflate, br
# content-type: application/x-www-form-urlencoded; charset=UTF-8
# origin: https://kodik.info
# referer: https://kodik.info/seria/1234567/hash123foobar/720p?translations=false
# user-agent: Mozilla/5.0 (X11; Linux x86_64) ...
# x-requested-with: XMLHttpRequest


class KodikDefaults:
    # pattern for parse payload next /gvi entrypoint POST request
    data = dict(
        d=re.compile(r'"d":"(.*?)"'),
        d_sign=re.compile(r'"pd":"(.*?)"'),
        pd_sign=re.compile(r'"pd_sign":"(.*?)"'),
        ref=re.compile(r'"ref":"(.*?)"'),
        ref_sign=re.compile(r'"ref_sign":"(.*?)"'),
        hash=re.compile(r"videoInfo\.hash = '(\w+)';"),
        id=re.compile(r'var videoId = "(\d+)"'),
        type=re.compile(r'var type = "(\w+)";'),
        bad_user=True,
        info="{}"
    )
    QUALITY = (720, 480, 360)
    RE_KODIK_REFERER = re.compile(r"data-code='(//\w+.\w{1,6}/\w{3,15}/\d+/\w+/\d{3}p)'>")
    KODIK_URL_VALIDATE = re.compile(r"//\w+\.\w{1,8}/\w{2,24}/\d+/\w+/")
    # default referer
    REFERER = "https://kodik.info/"


# aniboom.one request headers 12.07.22
# :authority: aniboom.one
# :method: GET
# :path: /embed/hash123foobar?episode=1&translation=2
# accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
# accept-language: ru-RU,ru
# referer: https://animego.org/
# upgrade-insecure-requests: 1
# user-agent: Mozilla/5.0 (X11; Linux x86_64) ...


class AniboomDefaults:
    RE_M3U8 = re.compile(r'"hls":"{\\"src\\":\\"(.*\.m3u8)\\"')
    RE_MPD = re.compile(r'"{\\"src\\":\\"(.*\.mpd)\\"')
    # parse master.m3u8, return [(quality, url), ...] results
    RE_M3U8_DATA = re.compile(
        r'''#EXT-X-STREAM-INF:BANDWIDTH=\d+,RESOLUTION=(\d+x\d+),CODECS=".*?",AUDIO=".*?"\s(.*?\.m3u8)''')
    QUALITY = (1080, 720, 480, 360)  # works only m3u8 format
    REFERER = "https://aniboom.one/"
    ACCEPT_LANG = "ru-RU"


# # Aniboom M3U8 object
class AniboomM3U8Data(NamedTuple):
    quality: str
    url_suffix: str
