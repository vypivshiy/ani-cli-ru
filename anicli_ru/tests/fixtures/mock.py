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
                "links": {360: [{"src": '=QDct5CM2MzX0NXZ09yL', "type": "application/x-mpegURL"}],
                          480: [{"src": '=QDct5CM4QzX0NXZ09yL', "type": "application/x-mpegURL"}],
                          720: [{"src": "=QDct5CMyczX0NXZ09yL", "type": "application/x-mpegURL"}]}
                }

ANIBOOM_RAW_RESPONSE = """<!DOCTYPE html><html lang="ru"><head><title>
                                                                                    Title name                                                            </title><!-- Required meta tags --><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no"><!-- Favicon --><link rel="apple-touch-icon" sizes="57x57" href="/favicons/apple-icon-57x57.png"><link rel="apple-touch-icon" sizes="60x60" href="/favicons/apple-icon-60x60.png"><link rel="apple-touch-icon" sizes="72x72" href="/favicons/apple-icon-72x72.png"><link rel="apple-touch-icon" sizes="76x76" href="/favicons/apple-icon-76x76.png"><link rel="apple-touch-icon" sizes="114x114" href="/favicons/apple-icon-114x114.png"><link rel="apple-touch-icon" sizes="120x120" href="/favicons/apple-icon-120x120.png"><link rel="apple-touch-icon" sizes="144x144" href="/favicons/apple-icon-144x144.png"><link rel="apple-touch-icon" sizes="152x152" href="/favicons/apple-icon-152x152.png"><link rel="apple-touch-icon" sizes="180x180" href="/favicons/apple-icon-180x180.png"><link rel="manifest" href="/manifest.json"><link rel="mask-icon" href="/favicons/safari-pinned-tab.svg" color="#5bbad5"><meta name="msapplication-TileColor" content="#da532c"><meta name="theme-color" content="#ffffff"><!-- Global site tag (gtag.js) - Google Analytics --><script async src="https://www.n0.com/gtag/js?id=UA-165559455-1"></script><script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            gtag('config', 'UA-165559455-1');
        </script><!-- Fonts --><link rel="stylesheet" href="https://fonts.n1.com/css?family=Open+Sans:300,400,600,700"><link rel="stylesheet" href="/build/334.7657e659.css"><script>const devicejs={isMobile:true,isTablet:false,platform:'Android'};</script><!-- Load dependent scripts --><script type="text/javascript" src="https://an.n3.ru/system/video-ads-sdk/adsdk.js"></script><script src="/build/runtime.9a71ee5d.js" async></script><script src="/build/26.9ca2c4a2.js" async></script><script src="/build/911.1db1c187.js" async></script><script src="/build/334.ee93b68d.js" async></script><script src="/build/player.ee696f97.js" async></script></head><body class="mobile"><div id="video" data-parameters="{&quot;id&quot;:&quot;Jo9ql8ZeqnW&quot;,&quot;error&quot;:&quot;\/video-error\/Jo9ql8ZeqnW&quot;,&quot;domain&quot;:&quot;animego.org&quot;,&quot;cdn&quot;:&quot;\/cdn\/foobarW&quot;,&quot;counter&quot;:&quot;\/counter\/foobar&quot;,&quot;duration&quot;:1511,&quot;poster&quot;:&quot;https:\/\/i1.fakeboom-img.com\/jo\/foobar\/mqdefault.jpg&quot;,&quot;thumbnails&quot;:&quot;https:\/\/i1.fakeboom-img.com\/jo\/foobar\/thumbnails\/thumbnails.vtt&quot;,&quot;dash&quot;:&quot;{\&quot;src\&quot;:\&quot;https:\\\/\\\/kekistan.cdn-fakeaniboom.com\\\/jo\\\/abcdef123\\\/111hash.mpd\&quot;,\&quot;type\&quot;:\&quot;application\\\/dash+xml\&quot;}&quot;,&quot;hls&quot;:&quot;{\&quot;src\&quot;:\&quot;https:\\\/\\\/kekistan.cdn-fakeaniboom.com\\\/jo\\\/abcdefg123\\\/master.m3u8\&quot;,\&quot;type\&quot;:\&quot;application\\\/x-mpegURL\&quot;}&quot;,&quot;quality&quot;:true,&quot;qualityVideo&quot;:1080,&quot;vast&quot;:true,&quot;country&quot;:&quot;RU&quot;,&quot;platform&quot;:&quot;Android&quot;,&quot;rating&quot;:&quot;16+&quot;}"></div><div class="vjs-contextmenu" id="contextmenu">aniboom.one</div></body></html>"""


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