from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .application import Application


class EventManager:
    """Manages application lifecycle events (startup and shutdown).

    This class handles the execution of startup and shutdown events for the application,
    providing a clean way to initialize and clean up resources.

    Args:
        app_ref: Reference to the main Application instance
    """

    def __init__(self, app_ref: "Application"):
        self._app_ref = app_ref

    @property
    def app_ref(self) -> "Application":
        """Application: Get the reference to the main application instance."""
        return self._app_ref

    @asynccontextmanager
    async def invoke_events(self):
        """Execute startup events, yield control, then execute shutdown events.

        Yields:
            None: Control is yielded between startup and shutdown events
        """
        try:
            for startup in self.app_ref.on_startup_events:
                await startup(self.app_ref.context)
            yield
        finally:
            for close in self.app_ref.on_close_events:
                await close(self.app_ref.context)
