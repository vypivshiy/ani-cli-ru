class MockResponseKodik:

    @property
    def text(self):
        return """<script>
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

    @staticmethod
    def json():
        return {"advert_script": "", "default": 360, "domain": "animeeee.kek", "ip": "192.168.0.1",
                "links": {360: [{"src": '=QDct5CM2MzX0NXZ09yL', "type": "application/x-mpegURL"}],
                          480: [{"src": '=QDct5CM4QzX0NXZ09yL', "type": "application/x-mpegURL"}],
                          720: [{"src": "=QDct5CMyczX0NXZ09yL", "type": "application/x-mpegURL"}]}
                }


class MockResponseAniboom:

    @property
    def text(self):
        return """<!DOCTYPE html><html lang="ru"><head><title> Glory Kekistan!                                          
                      ...<script> 
                      window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} gtag(
                      'js', new Date()); 

            gtag('config', 'UA-165559455-1'); </script><!-- Fonts --><link rel="stylesheet" 
            href="https://fonts.googleapis.com/css?family=Open+Sans:300,400,600,700"><link rel="stylesheet" 
            href="/build/334.7657e659.css"><script>const devicejs={isMobile:true,isTablet:false,
            platform:'Android'};</script><!-- Load dependent scripts --><script type="text/javascript" 
            src="https://an.yandex.ru/system/video-ads-sdk/adsdk.js"></script><script 
            src="/build/runtime.9a71ee5d.js" async></script><script src="/build/26.9ca2c4a2.js" 
            async></script><script src="/build/911.1db1c187.js" async></script><script src="/build/334.6177734e.js" 
            async></script><script src="/build/player.ee696f97.js" async></script></head><body class="mobile"><div 
            id="video" data-parameters="{&quot;id&quot;:&quot;9G1MJA2kqV8&quot;,
            &quot;error&quot;:&quot;\/video-error\/9G1MJA2kqV8&quot;,&quot;domain&quot;:&quot;animego.org&quot;,
            &quot;cdn&quot;:&quot;\/cdn\/9G1MJA2kqV8&quot;,&quot;counter&quot;:&quot;\/counter\/9G1MJA2kqV8&quot;,
            &quot;duration&quot;:1450,&quot;poster&quot;:&quot;https:\/\/i1.boom-img.com\/9g\/9G1MJA2kqV8\/mqdefault
            .jpg&quot;,&quot;thumbnails&quot;:&quot;https:\/\/i1.boom-img.com\/9g\/11111\/thumbnails
            \/thumbnails.vtt&quot;,&quot;dash&quot;:&quot;{
            \&quot;src\&quot;:\&quot;https:\\\/\\\/kekistan.ddd-anibywm.lol\\\/9g\\\/appletosh14\\\/62673ff3755441.mpd
            \&quot;,\&quot;type\&quot;:\&quot;application\\\/dash+xml\&quot;}&quot;,&quot;hls&quot;:&quot;{
            \&quot;src\&quot;:\&quot;https:\\\/\\\/kekistan.ddd-anibywm.lol\\\/9g\\\/appletosh14\\\/master.m3u8\&quot;,
            \&quot;type\&quot;:\&quot;application\\\/x-mpegURL\&quot;}&quot;,&quot;quality&quot;:true,
            &quot;qualityVideo&quot;:1080,&quot;vast&quot;:true,&quot;country&quot;:&quot;RU&quot;,
            &quot;platform&quot;:&quot;Android&quot;,&quot;rating&quot;:&quot;16+&quot;}"></div><div 
            class="vjs-contextmenu" id="contextmenu">aniboom.one</div></body></html> """
