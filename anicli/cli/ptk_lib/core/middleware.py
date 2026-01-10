"""Middleware system for commands and FSM states"""

from typing import Any, Awaitable, Callable, List


class CommandMiddlewareManager:
    """Manages middleware execution for commands."""

    @staticmethod
    async def run_middleware_stack(
        ctx: Any, middleware_list: List[Callable], handler: Callable[[], Awaitable[Any]]
    ) -> Any:
        """Execute middleware in order, then the handler.

        Args:
            ctx: Context object passed to middleware functions
            middleware_list: List of middleware functions to execute
            handler: The final handler function to execute after middleware

        Returns:
            The result of the handler function
        """
        if not middleware_list:
            return await handler()

        async def _chain(index: int):
            if index >= len(middleware_list):
                return await handler()
            mw = middleware_list[index]
            return await mw(ctx, lambda: _chain(index + 1))

        return await _chain(0)


class FSMMiddlewareManager:
    """Manages middleware execution for FSM sessions and states."""

    @staticmethod
    async def run_middleware_stack(
        ctx: Any, middleware_list: List[Callable], handler: Callable[[], Awaitable[Any]]
    ) -> Any:
        """Execute middleware in order, then the handler.

        Args:
            ctx: Context object passed to middleware functions
            middleware_list: List of middleware functions to execute
            handler: The final handler function to execute after middleware

        Returns:
            The result of the handler function
        """
        if not middleware_list:
            return await handler()

        async def _chain(index: int):
            if index >= len(middleware_list):
                return await handler()
            mw = middleware_list[index]
            return await mw(ctx, lambda: _chain(index + 1))

        return await _chain(0)
