"""base prototype architecture for anicli extractor

Extractor works schema:
    [Extractor]------------------download TODO add standard work implementation for download method
        | search()/ongoing()        |
        V                           |
  [SearchResult | Ongoing]          |
         | anime()                  |
         V                          |
    [AnimeInfo]                     |
        | episode()                 |
        V                           |
    [Episodes]                      |
        | video()                   |
        V                           |
    [Video] <-----------------------

"""
from anicli_api._http import BaseAsyncExtractorHttp, BaseSyncExtractorHttp


class AnimeHTTP(BaseSyncExtractorHttp):
    def search(self, query: str, *args, **kwargs):
        raise NotImplementedError

    def episode(self, *args, **kwargs):
        raise NotImplementedError

    def anime(self, *args, **kwargs):
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
        return f"[{self.__class__.__name__}] " + ", ".join((f"{k}={v}" for k, v in self.dict().items()))


class BaseSearchResult(BaseModel):
    HTTP: AnimeHTTP = NotImplemented
    HTTP_ASYNC: AnimeHTTPAsync = NotImplemented

    def anime(self):
        raise NotImplementedError


class BaseOngoing(BaseModel):
    HTTP: AnimeHTTP = NotImplemented
    HTTP_ASYNC: AnimeHTTPAsync = NotImplemented

    def anime(self):
        raise NotImplementedError


class BaseEpisode(BaseModel):
    HTTP: AnimeHTTP = NotImplemented
    HTTP_ASYNC: AnimeHTTPAsync = NotImplemented

    def videos(self):
        raise NotImplementedError

    def video(self):
        raise NotImplementedError


class BaseAnimeInfo(BaseModel):
    HTTP: AnimeHTTP = NotImplemented
    HTTP_ASYNC: AnimeHTTPAsync = NotImplemented

    def episodes(self):
        raise NotImplementedError

    def episode(self, num: int):
        raise NotImplementedError


class BaseVideo(BaseModel):
    HTTP: AnimeHTTP = NotImplemented
    HTTP_ASYNC: AnimeHTTPAsync = NotImplemented

    def link(self):
        raise NotImplementedError
