from base64 import b64encode

import pytest
from requests import Session

from anicli_ru.tests.fixtures.mock import KODIK_RAW_RESPONSE
from anicli_ru.utils import Kodik


@pytest.mark.parametrize("url", ["//foobarbaz.com/anime_for_debils_4k.mp4",
                                 "https://foobarbaz.com/anime_for_debils_4k.mp4"])
def test_decode(url: str):
    url_encode = b64encode(url.encode()).decode()[::-1]
    if not url.startswith("https"):
        assert Kodik.decode(url_encode) == f"https:{url}"
    else:
        assert Kodik.decode(url_encode) == url


def test_parse_payload():
    k = Kodik(Session())
    data, url = k.parse_payload(KODIK_RAW_RESPONSE, "foobar.com")
    assert url.startswith("fakeplayer.com/go/seria/12345")
    assert data.get("d") == "animeeee.kek"
    assert data.get("d_sign") == "hash0000000"
    assert data.get("ref") == "foobar.com"
    assert data.get("hash") == "h123a739s719hfoo"
    assert data.get("id") == "12345"
    assert data.get("bad_user") is True


@pytest.mark.parametrize("player_url", ["https://fakekodik.fake/seria/0/0h1as2h01234567/720p?foobar=baz",
                                        "//not_real_kodik.ru/seria/1/0h1as2h7654321/720p",
                                        "aniloh.fake/seria/1/0h1as2h7654321/720p"])
def test_get_api_url(player_url):
    url = Kodik(Session()).get_api_url(player_url)
    assert url.startswith("https") and url.endswith("/gvi")
