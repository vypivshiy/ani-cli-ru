"""Simple video redirect server.

Useful for redirecting the video stream to a video player where there is no way to set headers

Note:
    This implementation for standalone clients and is not suitable for production
"""
from urllib.parse import unquote_plus
import json
from ast import literal_eval
from typing import Optional, Iterable

from flask import Flask, Response, request
import httpx
import re

from anicli.server.parser import m3u8_stream_segments, m3u8_parse_manifest, mp4_stream


flask_app = Flask("POC Redirect video server")


@flask_app.route('/')
def restream_video():
    url = request.args.get('url')
    headers = request.args.get('headers')
    if not url:
        return 400, "url param required"
    headers = literal_eval(headers) if headers else {}
    resp = httpx.head(url, follow_redirects=True, headers=headers)
    if resp.is_success:
        if ".m3u8" in url:
            iterator = m3u8_stream_segments(url, headers)
        elif ".mp4" in url:
            iterator = mp4_stream(url, headers)
        elif ".mpd" in url:
            return 400, "Coming soon"
        else:
            return 400, "Unsupported type"
        return Response(iterator,
                        content_type=resp.headers["content-type"],
                        status=200)
    return resp.status_code, resp.content


if __name__ == '__main__':
    #tst_url = 'https://harris.yagami-light.com/lk/lk8qWJADdmo/master.m3u8'
    #tst_headers = {'Referer': 'https://aniboom.one/', 'Accept-Language': 'ru-RU', 'Origin': 'https://aniboom.one', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}
    #videos = m3u8_parse_manifest(tst_url, tst_headers)
    flask_app.run(debug=True, port=10007)
