from base64 import b64encode

import pytest
from requests import Session

from anicli_ru.utils import Kodik


KODIK_RAW_RESPONSE = """<script>
var iframe = document.createElement("iframe");
iframe.src = "//fakeplayer.com/go/seria/12345/h123a739s719hfoo/720p?d=animeeee.kek&d_sign=hash0000000&pd=fakeplayer.com&pd_sign=hash111&ref=https%3A%2F%2Fanimeeee.kek%2F&ref_sign=hash111&min_age=99";
iframe.id = "player-iframe";
iframe.width = "100%";
iframe.height = "100%";
iframe.frameBorder = "0";
iframe.allowFullscreen = true;
iframe.allow = "autoplay *; fullscreen *";
...
"""


KODIK_API_JSON = {"advert_script": "", "default": 360, "domain": "animeeee.kek", "ip": "192.168.0.1",
                "links": {"360": [{"src": '=QDct5CM2MzX0NXZ09yL', "type": "application/x-mpegURL"}],
                          "480": [{"src": '=QDct5CM4QzX0NXZ09yL', "type": "application/x-mpegURL"}],
                          "720": [{"src": "=QDct5CMyczX0NXZ09yL", "type": "application/x-mpegURL"}]}
                }


@pytest.fixture()
def mock_kodik(monkeypatch):
    def return_raw_kodik_response(*args, **kwargs):
        return KODIK_RAW_RESPONSE

    def return_api_kodik_response(*args, **kwargs):
        return KODIK_API_JSON["links"]
    # mock return status_code for test set quality

    def return_response_status_code(*args, **kwargs):
        return True

    monkeypatch.setattr(Kodik, "_get_raw_payload", return_raw_kodik_response)
    monkeypatch.setattr(Kodik, "_get_kodik_video_links", return_api_kodik_response)
    monkeypatch.setattr(Kodik, "_is_not_404_code", return_response_status_code)
    return Kodik


@pytest.mark.parametrize("player_url,quality,result",
                         [("https://kodikfake.kekis/seria/00/foobar/100p", 720, "https://test_720.mp4"),
                          ("https://kodikfake.kekis/seria/00/foobar/100p", 480, "https://test_480.mp4"),
                          ("https://kodikfake.kekis/seria/00/foobar/100p", 360, "https://test_360.mp4"),
                          ("https://kodikfake.kekis/seria/00/foobar/100p", 123, "https://test_720.mp4"),
                          ("https://kodikfake.kekis/seria/00/foobar/100p", -8, "https://test_720.mp4")])
def test_parse_video(mock_kodik, player_url, quality, result):
    assert mock_kodik.parse(player_url, quality=quality) == result


@pytest.mark.parametrize("url_encoded,result",
                         [('0AXbusGNfNHbpJWZk9lcvZ2Xl1WauF2Lt92YuoXYiJXYi92bm9yL',
                           "https://foobarbaz.com/anime_for_debils_4k.mp4"),

                          ("'0AXbusGNfNHbpJWZk9lcvZ2Xl1WauF2Lt92YuoXYiJXYi92bm9yL6MHc0RHa'",
                           "https://foobarbaz.com/anime_for_debils_4k.mp4")])
def test_decode(url_encoded, result):
    assert Kodik.decode(url_encoded) == result
