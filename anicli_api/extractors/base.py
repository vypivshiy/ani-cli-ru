"""base prototype architecture for anicli extractor"""
from typing import Dict, Union
import re

from anicli_api._http import BaseAsyncExtractorHttp, BaseSyncExtractorHttp
from anicli_api.re_models import ReBaseField


class AnimeHTTP(BaseSyncExtractorHttp):
    def search(self, query: str, *args, **kwargs):
        raise NotImplementedError

    def episode(self, *args, **kwargs):
        raise NotImplementedError

    def ongoing(self, *args, **kwargs):
        raise NotImplementedError

    def download(self, *args, **kwargs):
        raise NotImplementedError


class AnimeHTTPAsync(BaseAsyncExtractorHttp):
    async def search(self, query: str, *args, **kwargs):
        raise NotImplementedError

    async def episode(self, *args, **kwargs):
        raise NotImplementedError

    async def ongoing(self, *args, **kwargs):
        raise NotImplementedError

    async def download(self, *args, **kwargs):
        raise NotImplementedError


class AnimeExtractor:
    HTTP: AnimeHTTP = NotImplemented

    def search(self, query: str, *args, **kwargs):
        return self.HTTP.search(query)

    def ongoing(self, *args, **kwargs):
        return self.HTTP.ongoing()

    def download(self, *args, **kwargs):
        return self.HTTP.download()


class BaseModel:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def dict(self):
        return {k: getattr(self, k) for k in self.__annotations__
                if not k.startswith("__") and not k.endswith("__")}

    def __repr__(self):
        return f"[{self.__class__.__name__}] " + ", ".join((f"<{k}>={v}" for k,v in self.dict().items()))


class BaseSearchResult(BaseModel):
    HTTP: Union[AnimeHTTP, AnimeHTTPAsync] = NotImplemented

    def episodes(self):
        raise NotImplementedError


class BaseOngoing(BaseModel):
    HTTP: Union[AnimeHTTP, AnimeHTTPAsync] = NotImplemented

    def episodes(self):
        raise NotImplementedError


class BaseEpisode(BaseModel):
    HTTP: Union[AnimeHTTP, AnimeHTTPAsync] = NotImplemented

    def videos(self):
        raise NotImplementedError
