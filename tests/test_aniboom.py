try:
    from html.parser import unescape
except ImportError:
    from html import unescape


from tests.fixtures.mock import ANIBOOM_RAW_RESPONSE, ANIBOOM_M3U8_DATA
from anicli_ru.utils import Aniboom


def test_url_parser():
    mpd, = Aniboom.RE_MPD.findall(unescape(ANIBOOM_RAW_RESPONSE))
    m3u8, = Aniboom.RE_M3U8.findall(unescape(ANIBOOM_RAW_RESPONSE))
    assert m3u8.replace("\\", "") == 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/master.m3u8'
    assert mpd.replace("\\", "") == 'https://kekistan.cdn-fakeaniboom.com/jo/abcdef123/111hash.mpd'


def test_m3u8_parser():
    data = Aniboom.RE_M3U8_DATA.findall(ANIBOOM_M3U8_DATA)
    print()
    assert data[0] == ('640x360', 'media_0.m3u8')
    assert data[1] == ('854x480', 'media_2.m3u8')
    assert data[2] == ('1280x720', 'media_4.m3u8')
    assert data[3] == ('1920x1080', 'media_6.m3u8')