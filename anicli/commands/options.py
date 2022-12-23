from typing import List

from anicli_api.base_decoder import MetaVideo
from anicli_api.extractors import animego

EXTRACTOR = animego.Extractor()
PLAYER = "mpv"


def mpv_attrs(video: MetaVideo) -> List[str]:
    if video.extra_headers:
        # --http-header-fields='Field1: value1','Field2: value2'
        headers = ",".join([f"{k}: {v}" for k, v in video.extra_headers.items()])
        param = f'-http-header-fields="{headers}"'
        return [PLAYER, video.url, param]
    return [PLAYER, video.url]