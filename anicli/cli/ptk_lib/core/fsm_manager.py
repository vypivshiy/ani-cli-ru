"""FSM management: registration and state execution"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from rich.console import Console

from .middleware import FSMMiddlewareManager
from .types import FSMRoute, FSMState

if TYPE_CHECKING:
    from .application import Application
    from .fsm import BaseFSM


class FSMManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.fsm_routes: Dict[str, FSMRoute] = {}
        self._fsm_aliases: Dict[str, str] = {}  # alias -> route_key
        self.console = Console()

    def register(self, route: FSMRoute) -> None:
        """Register an FSM route."""
        self.fsm_routes[route.key] = route
        for alias in route.aliases:
            if alias in self.fsm_routes or alias in self._fsm_aliases:
                msg = f"FSM alias '{alias}' already registered"
                raise ValueError(msg)
            self._fsm_aliases[alias] = route.key

    def get_route(self, key: str) -> Optional[FSMRoute]:
        """Get FSM route by key or alias."""
        if key in self.fsm_routes:
            return self.fsm_routes[key]
        if key in self._fsm_aliases:
            return self.fsm_routes[self._fsm_aliases[key]]
        return None

    async def create_fsm_session(
        self,
        route_key: str,
        initial_state: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "BaseFSM":
        """Create a new FSM session instance."""
        route = self.get_route(route_key)
        if route is None:
            msg = f"FSM route '{route_key}' not found"
            raise ValueError(msg)

        actual_initial = initial_state or route.initial_state
        if actual_initial not in route.states:
            msg = f"Initial state '{actual_initial}' not in FSM '{route_key}'"
            raise ValueError(msg)

        fsm_instance = route.fsm_class(
            app=self.app,
            route_key=route_key,
            context=context or {},
        )
        await fsm_instance._enter_state(actual_initial)
        return fsm_instance

    async def execute_state(
        self,
        fsm_instance: "BaseFSM",
        state: "FSMState",
        user_input: str,
    ) -> None:
        """Execute an FSM state handler."""

        async def _call_handler():
            # Validate (this should already be done by PromptSession.validator,
            # but we double-check for safety)
            if state.validator:
                is_valid = state.validator(user_input, fsm_instance.context)
                if not is_valid:
                    self.console.print("[red]Validation failed[/red]")
                    return

            # Determine if handler expects FSM instance (self) — it always does
            # So we pass (self, user_input)

            # 1. currently, is not implemented custom str parser as in CommandRoute object

            # 2. not required create new context:
            # "FsmState" has access to the context from the "BaseFSM" instance

            args_to_pass = (fsm_instance, user_input)
            kwargs_to_pass = {}
            return await state.handler(*args_to_pass, **kwargs_to_pass)

        # middleware_manager = get_fsm_middleware_manager()
        await FSMMiddlewareManager.run_middleware_stack(fsm_instance.context, state.middleware, _call_handler)
