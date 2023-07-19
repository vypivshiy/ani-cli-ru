"""
PoC  redirect video server to player
how it works:
1 send to GET request to http://127.0.0.1:5000 with url=<encoded url>
2. replace relative to absolute path chunk
Examole:
    hls:seg-1-v1-a1.ts\n#EXTINF:6.000,\n./360.mp4: to
... hls:seg-1-v1-a1.ts\n#EXTINF:6.000,\nhttps://cloud.kodik-storage.com/useruploads/.../360.mp4: ...
3. return chunk

Example command:
# mpv "http://127.0.0.1:5000?url=https%3A%2F%2Fcloud.kodik-storage.com%2Fuseruploads%2Fc6bef07a-041e-4bc8-baae-7e5e02650d52%2F28eae65063bb82ea20db1e67e4ca2125%3A2023071921%2F360.mp4%3Ahls%3Amanifest.m3u8"

"""
from typing import Optional

from flask import Flask, Response, request
import httpx
import re

app = Flask("POC Redirect video server")


def read_response(url: str, headers: Optional[dict] = None):
    headers = headers or {}
    with httpx.stream("GET", url, follow_redirects=True, headers=headers) as response:
        target_url = str(response.url)
        for chunk in response.iter_text():
            # replace relative path to absolute
            new_chunk = re.sub(r"\./(\d+)\.mp4", target_url, chunk)
            yield new_chunk.encode()


@app.route('/')
def restream_video():
    url = request.args.get('url')
    headers = request.args.get('headers')
    if not url:
        return 400
    resp1 = httpx.get(url, follow_redirects=True)
    return Response(read_response(url),
                    content_type=resp1.headers["content-type"],
                    status=resp1.status_code)


if __name__ == '__main__':
    app.run(debug=True)
