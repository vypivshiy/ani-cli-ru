import pytest
import httpx

from anicli_api.decoders import Aniboom, Kodik, BaseDecoder

KODIK_RAW_RESPONSE = """
...
var type = "seria";
var videoId = "1025427";
var urlParams = '{"d":"animeeee.kek","d_sign":"d_signhash123","pd":"fakekodik.com","pd_sign":"pd_sign123hash","ref":"animeeee.kek","ref_sign":"ref_signhash123","translations":false}';
var autoResume = false;
var fullscreenLockOrientation = true
var videoInfo = {};
...
<td><div class='get_code_copy' data-code='//fakekodik.com/seria/123/hashfakeseria/720p'>TEST</div></td>
...

videoInfo.type = 'seria'; 
videoInfo.hash = 'b2f2a9d450ff2b2374d37c768e1b104e'; 
videoInfo.id = '1025427'; 
"""

KODIK_API_JSON = {"advert_script": "", "default": 360, "domain": "animeeee.kek", "ip": "192.168.0.1",
                  "links": {"360": [{"src": '=QDct5CM2MzX0NXZ09yL', "type": "application/x-mpegURL"}],
                            "480": [{"src": '=QDct5CM4QzX0NXZ09yL', "type": "application/x-mpegURL"}],
                            "720": [{"src": "=QDct5CMyczX0NXZ09yL", "type": "application/x-mpegURL"}]}
                  }

ANIBOOM_RAW_RESPONSE = """
<div id="video" data-parameters="{&quot;id&quot;:&quot;Jo9ql8ZeqnW&quot;,&quot;error&quot;:&quot;\/video-error\/Jo9ql8ZeqnW&quot;,&quot;domain&quot;:&quot;animego.org&quot;,&quot;cdn&quot;:&quot;\/cdn\/foobarW&quot;,&quot;counter&quot;:&quot;\/counter\/foobar&quot;,&quot;duration&quot;:1511,&quot;poster&quot;:&quot;https:\/\/i1.fakeboom-img.com\/jo\/foobar\/mqdefault.jpg&quot;,&quot;thumbnails&quot;:&quot;https:\/\/i1.fakeboom-img.com\/jo\/foobar\/thumbnails\/thumbnails.vtt&quot;,&quot;dash&quot;:&quot;{\&quot;src\&quot;:\&quot;https:\\\/\\\/kekistan.cdn-fakeaniboom.com\\\/jo\\\/abcdef123\\\/111hash.mpd\&quot;,\&quot;type\&quot;:\&quot;application\\\/dash+xml\&quot;}&quot;,&quot;hls&quot;:&quot;{\&quot;src\&quot;:\&quot;https:\\\/\\\/kekistan.cdn-fakeaniboom.com\\\/jo\\\/abcdefg123\\\/master.m3u8\&quot;,\&quot;type\&quot;:\&quot;application\\\/x-mpegURL\&quot;}&quot;,&quot;quality&quot;:true,&quot;qualityVideo&quot;:1080,&quot;vast&quot;:true,&quot;country&quot;:&quot;RU&quot;,&quot;platform&quot;:&quot;Android&quot;,&quot;rating&quot;:&quot;16+&quot;}"></div><div class="vjs-contextmenu" id="contextmenu">aniboom.one</div>
"""

ANIBOOM_M3U8_DATA = """#EXTM3U
#EXT-X-VERSION:7
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="group_A1",NAME="audio_1",DEFAULT=YES,URI="media_1.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=593867,RESOLUTION=640x360,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"
media_0.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=943867,RESOLUTION=854x480,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"
media_2.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1593867,RESOLUTION=1280x720,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"
media_4.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2893867,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"
media_6.m3u8
"""


@pytest.fixture()
def mock_kodik():
    class MockKodik(Kodik): ...

    def handler(request: httpx.Request):
        if request.method == "GET":
            return httpx.Response(200, text=KODIK_RAW_RESPONSE)
        return httpx.Response(200, json=KODIK_API_JSON)

    transport = httpx.MockTransport(handler)
    kodik = MockKodik
    kodik.HTTP._transport = transport
    return kodik


@pytest.fixture()
def mock_aniboom():
    class MockAniboom(Aniboom): ...

    def handler(request: httpx.Request):
        if str(request.url).endswith("m3u8"):
            return httpx.Response(200, text=ANIBOOM_M3U8_DATA)
        return httpx.Response(200, text=ANIBOOM_RAW_RESPONSE)

    transport = httpx.MockTransport(handler)
    aniboom = MockAniboom
    aniboom.HTTP._transport = transport
    return aniboom


@pytest.mark.parametrize("url_encoded,result",
                         [('0AXbusGNfNHbpJWZk9lcvZ2Xl1WauF2Lt92YuoXYiJXYi92bm9yL',
                           "https://foobarbaz.com/anime_for_debils_4k.mp4"),

                          ("'0AXbusGNfNHbpJWZk9lcvZ2Xl1WauF2Lt92YuoXYiJXYi92bm9yL6MHc0RHa'",
                           "https://foobarbaz.com/anime_for_debils_4k.mp4")])
def test_decode(url_encoded, result):
    assert Kodik.decode(url_encoded) == result


def test_equal_kodik():
    assert "https://kodikfake.kekis/seria/00/foobar/100p" == Kodik()
    assert "https://google.com" != Kodik()


def test_equal_aniboom():
    assert "https://aniboom.one/embed/asdasdasfasf" == Aniboom()
    assert "https://google.com" != Aniboom


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
            return "mock"

        def __eq__(self, other: str):  # type: ignore
            return True

    assert "foobar" == MyDecoder()
    assert MyDecoder.parse("aaaaa") == "test123"
