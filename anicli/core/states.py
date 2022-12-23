from __future__ import annotations
from enum import Enum
from typing import Any, Dict, Optional


class StateDispenser:
    def __init__(self):
        self.state: Optional[BaseState] = None
        self.data = {}

    def set(self, state: BaseState):
        self.state = state

    def finish(self):
        self.clear()
        self.state = None

    def clear(self):
        self.data.clear()

    def __bool__(self):
        return bool(self.state)

    def __iter__(self):
        return self.data.__iter__()

    def __contains__(self, item):
        return item in self.data

    def update_data(self, data: Dict[str, Any]):
        self.data.update(data)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __str__(self):
        return f"State: {self.state} storage data: {self.data}"


class BaseState(str, Enum):
    ...
