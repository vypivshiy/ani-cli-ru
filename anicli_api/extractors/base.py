"""base prototype architecture for anicli extractor"""
from dataclasses import dataclass

from anicli_api._http import BaseAsyncExtractorHttp, BaseSyncExtractorHttp

# TODO: ???


class Extractor(BaseSyncExtractorHttp):
    def search(self, query: str):
        raise NotImplementedError

    def episode(self):
        raise NotImplementedError

    def ongoing(self):
        raise NotImplementedError


class AsyncExtractor(BaseAsyncExtractorHttp):
    async def search(self, query: str, *args, **kwargs):
        raise NotImplementedError

    async def episode(self, *args, **kwargs):
        raise NotImplementedError

    async def ongoing(self, *args, **kwargs):
        raise NotImplementedError


@dataclass
class BaseModel:
    ...


class SearchResult(BaseModel):
    ...


class Ongoing(BaseModel):
    ...


class Episode(BaseModel):
    ...


class Video(BaseModel):
    ...
