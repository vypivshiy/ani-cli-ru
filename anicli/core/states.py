from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, Hashable, Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")


class BaseStorage:
    def __init__(self):
        self._data: Dict[Hashable, Any] = {}

    def __iter__(self):
        return self._data.__iter__()

    def __contains__(self, item):
        return item in self._data

    def update(self, data: Dict):
        self._data.update(data)

    def items(self):
        return self._data.items()

    def clear(self):
        self._data.clear()

    def get(self, key):
        return self._data.get(key, None)

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __str__(self):
        return f"Data: {self._data}"


class Storage(BaseStorage):
    def __init__(self):
        super().__init__()
        self._data: Dict[BaseState, Dict[str, Any]] = {}


class StorageParams(BaseStorage):
    def __init__(self):
        super().__init__()
        self._data: Dict[BaseState, Tuple]


class StateDispenser:
    """Standard FSM class"""

    def __init__(self):
        self.state: Optional[BaseState] = None
        self.storage = Storage()
        self.storage_params = StorageParams()

    def set(self, state: BaseState):
        """Set state"""
        self.state = state

    def finish(self):
        """finish state and clear all storage data"""
        self.storage.clear()
        self.storage_params.clear()
        self.state = None

    @staticmethod
    def _create_hash_key(obj: Any) -> int:
        if isinstance(obj, Hashable):
            key = hash(obj)
        elif isinstance(obj, dict):
            key = hash(obj.keys())
        elif isinstance(obj, Sequence):
            key = hash(tuple(obj))
        else:
            raise TypeError(f"`{obj}` failed create hash key")
        return key

    def cache_object(self, key: Any, obj: Any):
        """Cache object to FSM storage"""
        key = self._create_hash_key(key)
        if self.storage.get(key):
            return
        self.storage[key] = obj

    def _get_cache(self, key: Any):
        key = self._create_hash_key(key)
        return self.storage.get(key)

    def get_from_cache(self, key: T, function: Callable[[], T]) -> T:
        """get values from cache. if not get, cache objects and return values"""
        if not (results := self._get_cache(key)):
            results = function()
            self.cache_object(key, results)
        return results

    def update(self, data: Dict):
        self.storage.update(data)

    def get(self, key):
        return self.storage.get(key)

    def __repr__(self):
        return f"State={self.state} which {self.storage}"

    def __getitem__(self, item):
        return self.storage[item]

    def __setitem__(self, key, value):
        self.storage[key] = value

    def __bool__(self):
        return bool(self.state)

    def __str__(self):
        return f"Storage: {self.storage} Params: {self.storage_params}"


class BaseState(str, Enum):
    ...
