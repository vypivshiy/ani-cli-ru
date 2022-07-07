from html import unescape
from typing import Tuple

import pytest

from anicli_ru.utils import Aniboom
from anicli_ru.utils.aniboom import AniboomM3U8Data


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
def mock_aniboom(monkeypatch):
    def return_aniboom_player_response(*args, **kwargs) -> str:
        return unescape(ANIBOOM_RAW_RESPONSE)

    def return_m3u8_video_data(*args, **kwargs) -> Tuple[AniboomM3U8Data, ...]:
        return tuple(AniboomM3U8Data(qual, url) for qual, url in Aniboom.RE_M3U8_DATA.findall(ANIBOOM_M3U8_DATA))

    monkeypatch.setattr(Aniboom, "_get_aniboom_html_response", return_aniboom_player_response)
    monkeypatch.setattr(Aniboom, "_parse_m3u8", return_m3u8_video_data)
    return Aniboom


def test_parse_mpd(mock_aniboom):
    assert Aniboom.parse("aniboom-fake", mpd=True) == 'https://kekistan.cdn-fakeaniboom.com/jo/abcdef123/111hash.mpd'


def test_parse_m3u8(mock_aniboom):
    assert Aniboom.parse("aniboom-fake") == 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/master.m3u8'


@pytest.mark.parametrize("quality, result", [(1080, ('media_6.m3u8', 'master.m3u8')),
                                             (720, 'media_4.m3u8'),
                                             (480, 'media_2.m3u8'),
                                             (360, 'media_0.m3u8'),
                                             (123, ('media_6.m3u8', 'master.m3u8'))])
def test_parse_m3u8_quality(mock_aniboom, quality, result):
    assert Aniboom.parse("aniboom-fake", quality=quality).endswith(result)

