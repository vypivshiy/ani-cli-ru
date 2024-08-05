from typing import TYPE_CHECKING, Union, Iterable, List

import sys

if TYPE_CHECKING:
    from anicli_api.base import BaseSource, BaseSearch, BaseEpisode, BaseOngoing, Video

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

ANICLI_API_ITEM: TypeAlias = Union['BaseSearch', 'BaseOngoing', 'BaseEpisode', 'BaseSource', 'Video']
ANICLI_API_ITEMS = Iterable[ANICLI_API_ITEM]
SEARCH_OR_ONGOING: TypeAlias = Union['BaseSearch', 'BaseOngoing']
LIST_SEARCH_OR_ONGOING = List[SEARCH_OR_ONGOING]
