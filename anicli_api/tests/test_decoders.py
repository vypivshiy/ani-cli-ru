import pytest
import httpx

from anicli_api.tests import mock_kodik, mock_aniboom  # type: ignore
from anicli_api.decoders import Aniboom, Kodik, BaseDecoder


@pytest.mark.parametrize("url_encoded,result",
                         [('0AXbusGNfNHbpJWZk9lcvZ2Xl1WauF2Lt92YuoXYiJXYi92bm9yL',
                           "https://foobarbaz.com/anime_for_debils_4k.mp4"),

                          ("'0AXbusGNfNHbpJWZk9lcvZ2Xl1WauF2Lt92YuoXYiJXYi92bm9yL6MHc0RHa'",
                           "https://foobarbaz.com/anime_for_debils_4k.mp4")])
def test_decode(url_encoded, result):
    assert Kodik.decode(url_encoded) == result


def test_eq_cmp_kodik():
    assert "https://kodikfake.kekis/seria/00/foobar/100p" == Kodik()


def test_ne_cmp_kodik():
    assert "https://google.com" != Kodik()


def test_eq_cmp_aniboom():
    assert "https://aniboom.one/embed/asdasdasfasf" == Aniboom()


def test_ne_cmp_aniboom():
    assert "https://google.com" != Aniboom()


def test_parse_kodik(mock_kodik):
    result = mock_kodik.parse("https://kodikfake.fake/seria/00/foobar/100p")
    assert result == {'360': 'https://test_360.mp4', '480': 'https://test_480.mp4', '720': 'https://test_720.mp4'}


def test_parse_aniboom(mock_aniboom):
    result = mock_aniboom.parse("https://aniboom.one/embed/fake_aniboom_la-la-la")
    assert result == {'m3u8': {
        '360': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_0.m3u8',
        '480': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_2.m3u8',
        '720': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_4.m3u8',
        '1080': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_6.m3u8'},
        'mpd': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdef123/111hash.mpd'}


def test_custom_decoder():
    class MyDecoder(BaseDecoder):
        @classmethod
        def parse(cls, url: str):
            return "test123"

        @classmethod
        async def async_parse(cls, url: str):
            ...

        def __eq__(self, other: str):  # type: ignore
            return "foobar" in other

    assert "foobar" == MyDecoder()
    assert "bazfoo" != MyDecoder()
    assert MyDecoder.parse("aaaaa") == "test123"
