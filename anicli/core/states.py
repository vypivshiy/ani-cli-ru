from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Hashable, Optional, Sequence, Tuple, TypeVar

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


class MemoryCacheStorage(BaseStorage):
    @staticmethod
    def _create_hash_key(obj: T) -> int:
        if isinstance(obj, Hashable):
            key = hash(obj)
        elif isinstance(obj, dict):
            key = hash(obj.keys())
        elif isinstance(obj, Sequence):
            key = hash(tuple(obj))
        else:
            raise TypeError(f"`{obj}` `{type(obj)}` failed create hash key")
        return key

    def __setitem__(self, key: Any, value: Any):
        """Cache object in FSM storage without return"""
        key = self._create_hash_key(key)
        self._data[key] = value

    def __getitem__(self, item):
        item = self._create_hash_key(item)
        return self._data[item]

    def get(self, key) -> T:
        """get value from cache."""
        key = self._create_hash_key(key)
        return self._data.get(key, None)


class StateDispenser:
    """Standard FSM class"""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.state: Optional[BaseState] = None
        self.storage = Storage()
        self.storage_params = StorageParams()
        self.cache = MemoryCacheStorage()

    def set(self, state: BaseState):
        """Set state"""
        self.state = state

    def finish(self):
        """finish state and clear all storage data"""
        self.storage.clear()
        self.storage_params.clear()
        self.cache.clear()
        self.state = None

    def update(self, data: Dict):
        self.storage.update(data)

    def get(self, key):
        return self.storage.get(key)

    def __repr__(self):
        return f"State={self.state} Cache={self.cache} Storage={self.storage} StorageParams={self.storage_params}"

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
