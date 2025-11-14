from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .application import Application


class EventManager:
    def __init__(self, app_ref: "Application"):
        self._app_ref = app_ref

    @property
    def app_ref(self) -> "Application":
        return self._app_ref

    @asynccontextmanager
    async def invoke_events(self):
        try:
            for startup in self.app_ref.on_startup_events:
                await startup(self.app_ref.context)
            yield
        finally:
            for close in self.app_ref.on_close_events:
                await close(self.app_ref.context)
