"""Finite State Machine implementation"""

import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Generic, List, Optional, Tuple, TypedDict, Union

from anicli.cli.ptk_lib.core.types import FSMState

from .types import CtxT, FSMContext

if TYPE_CHECKING:
    from .application import Application


class FsmNavigationCommand(TypedDict):
    description: str
    """описание для compleations"""
    handler: str
    """имя метода"""


class BaseFSM(ABC, Generic[CtxT]):
    """Base class for all FSM sessions.

    Each instance represents one active FSM session with its own context.

    Args:
        app: Reference to the main Application instance
        route_key: Key identifying the FSM route
        context: Initial context data for the FSM session
    """

    NAVIGATION_COMMANDS: ClassVar[Dict[str, FsmNavigationCommand]] = {
        "..": {"handler": "_handle_go_back", "description": "Go back to previous state"},
        "~": {
            "handler": "_handle_stop",
            "description": "return to main menu",
        },
        "history": {"description": "[DEBUG] Show state history", "handler": "_handle_history"},
    }
    """magic constant for define commands for all states (used for manipulate FSM states)

    has next structure:
        {"<key>": {"handler": "{method_name}", "description": "{meta info for completer}"},
        ...
        }
    """

    def __init__(
        self,
        app: "Application",
        route_key: str,
        context: CtxT,
    ):
        """Initialize the FSM with application reference, route key, and context.

        Args:
            app: Reference to the main Application instance
            route_key: Key identifying the FSM route
            context: Initial context data for the FSM session
        """
        self._app_ref = app
        self._route_key = route_key
        self.context = FSMContext(
            app=self._app_ref,
            _data=context,
            state_history=[],
            current_state=None,
        )
        self._prompt_vars: Dict[str, str] = {}

    # NAVIGATION COMMAND API
    def get_navigation_commands(self) -> Dict[str, FsmNavigationCommand]:
        """Get a copy of the navigation commands dictionary.

        Returns:
            Dictionary of navigation commands with their configurations
        """
        return self.NAVIGATION_COMMANDS.copy()

    def get_navigation_completions(self, current_text: str) -> List[Tuple[str, str]]:
        """Get navigation command completions that match the current input.

        Args:
            current_text: The current text being typed by the user

        Returns:
            List of tuples containing (command, description) that match the input
        """
        commands = self.get_navigation_commands()
        return [(cmd, config["description"]) for cmd, config in commands.items() if cmd.startswith(current_text)]

    def is_navigation_command(self, user_input: str) -> bool:
        """Check if the user input is a navigation command.

        Args:
            user_input: The user input to check

        Returns:
            True if the input is a navigation command, False otherwise
        """
        return user_input in self.get_navigation_commands()

    async def handle_navigation_command(self, user_input: str) -> bool:
        """Handle navigation commands like going back or stopping the FSM.

        Args:
            user_input: The navigation command to handle

        Returns:
            True if command was handled, False otherwise
        """
        commands = self.get_navigation_commands()
        if user_input not in commands:
            return False

        handler_name = commands[user_input]["handler"]
        handler = getattr(self, handler_name, None)

        if handler and callable(handler):
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()
            return True

        return False

    # default built-in impl
    async def _handle_go_back(self):
        """Navigate back to the previous state in the FSM.

        If there is no previous state to return to, the FSM session is exited.
        """
        success = await self.go_back()
        if not success:
            # If there's nowhere to go back to, exit the FSM
            await self.on_fsm_exit()
            self._app_ref._current_fsm = None
            self._app_ref.prompt_manager.reset_prompt_template()

    async def _handle_stop(self):
        """Stop the current FSM session and return to the main application."""
        await self.on_fsm_exit()
        self._app_ref._current_fsm = None
        self._app_ref.prompt_manager.reset_prompt_template()

    async def _handle_history(self):
        """Display the history of states visited in the current FSM session."""
        states = self.context.state_history[:]
        if self.context.current_state is not None:
            name = self.context.current_state.name
            states.append(name)
        path = " -> ".join(states)
        self._app_ref.console.print(f"[dim]Path: {path}[/dim]")

    # API, VALIDATORS CUSTOMISATION
    def get_dynamic_completions(self, state_name: str, current_text: str):
        """Get dynamic completions combining user-defined and navigation commands.

        Args:
            state_name: The name of the current state
            current_text: The current text being typed by the user

        Returns:
            Combined list of completions from both user-defined and navigation sources
        """
        user_completions = self._get_user_dynamic_completions(state_name, current_text)
        nav_completions = self._get_navigation_completions(current_text)
        # with meta info
        if user_completions is None or len(user_completions) == 0:
            return nav_completions

        elif len(user_completions) > 0 and isinstance(user_completions[0], tuple):
            return user_completions + nav_completions
        # apologize, its list of strings (remove descriptions)
        return user_completions + [i[0] for i in nav_completions]

    def get_dynamic_validator(self, state_name: str, user_input: str):
        """Validate user input using both navigation and user-defined validators.

        Args:
            state_name: The name of the current state
            user_input: The input provided by the user

        Returns:
            Boolean indicating if validation passed, or a string with an error message
        """
        # navigation always allow
        if self.is_navigation_command(user_input):
            return True

        # use overrided validator
        return self._get_user_dynamic_validator(state_name, user_input)

    def _get_navigation_completions(self, current_text: str):
        """Get navigation command completions that match the current input.

        Args:
            current_text: The current text being typed by the user

        Returns:
            List of tuples containing (command, description) that match the input
        """
        return [
            (cmd, description["description"])
            for cmd, description in self.NAVIGATION_COMMANDS.items()
            if cmd.startswith(current_text)
        ]

    @abstractmethod
    def _get_user_dynamic_completions(
        self, state_name: str, current_text: str
    ) -> Union[List[str], List[Tuple[str, str]]]:
        """Override this method to provide extra completions for the FSM.

        Note: Navigation commands from "NAVIGATION_COMMANDS" classvar are automatically added,
        no need to include them.

        Args:
            state_name: The name of the current state
            current_text: The current text being typed by the user

        Returns:
            List of completions as either:
                - List[str] -> word completion
                - List[Tuple[str, str]] -> word completion with meta
        """
        return []

    @abstractmethod
    def _get_user_dynamic_validator(self, state_name: str, user_input: str) -> Union[bool, str]:
        """Override this method to provide extra validations for the FSM.

        Note: Navigation commands from "NAVIGATION_COMMANDS" classvar are automatically allowed,
        no need to include them.

        Args:
            state_name: The name of the current state
            user_input: The input provided by the user

        Returns:
            - True - validation passed
            - False - validation error (default error message)
            - String - validation error, with custom error message
        """
        return True

    @property
    def app_ref(self) -> "Application[CtxT]":
        """Application: Get reference to the main application instance."""
        return self._app_ref

    @property
    def ctx(self) -> CtxT:
        """Get the FSM session's context data."""
        return self.context._data

    @property
    def route_key(self) -> str:
        """str: Get the key identifying this FSM route."""
        return self._route_key

    @property
    def current_state(self) -> Optional[FSMState]:
        """Optional[FSMState]: Get the current state of the FSM, or None if no state."""
        return self.context.current_state

    async def next_state(self, state_name: str) -> None:
        """Move to the next state, adding the current state to the history.

        Args:
            state_name: Name of the state to transition to
        """
        if self.context.current_state:
            self.context.state_history.append(self.context.current_state.name)
        await self._enter_state(state_name)

    async def jump_to(self, state_name: str) -> None:
        """Jump directly to a state without affecting the history.

        Args:
            state_name: Name of the state to jump to
        """
        await self._enter_state(state_name)

    async def go_back(self) -> bool:
        """Return to the previous state in the history.

        Returns:
            True if successfully returned to a previous state, False if no history
        """
        if not self.context.state_history:
            return False
        prev_state = self.context.state_history.pop()
        await self._enter_state(prev_state)
        return True

    async def _enter_state(self, state_name: str) -> None:
        """Enter a new state, executing exit and entry hooks if defined.

        Args:
            state_name: Name of the state to enter

        Raises:
            ValueError: If the state name is not found in the FSM
        """
        route = self._app_ref.fsm_manager.fsm_routes[self.route_key]
        if state_name not in route.states:
            msg = f"State '{state_name}' not found in FSM '{self.route_key}'"
            raise ValueError(msg)

        # Exit current state
        if self.context.current_state:
            current_state_obj = self.context.current_state
            if current_state_obj.on_exit:
                await current_state_obj.on_exit(self)

        # Enter new state
        new_state_obj = route.states[state_name]
        if new_state_obj.on_enter:
            await new_state_obj.on_enter(self)

        # Update context after on_enter to ensure any state changes in on_enter are preserved
        self.context.current_state = new_state_obj

        # Notify PromptManager to update prompt
        prompt_msg = new_state_obj.prompt_message
        if prompt_msg:
            self._app_ref.prompt_manager.set_prompt_template(prompt_msg)
            self._app_ref.prompt_manager.update_vars(self._prompt_vars)

    def set_prompt_var(self, key: str, value: Any) -> None:
        """Set a variable for dynamic prompt formatting (e.g., {episode}).

        Args:
            key: Name of the variable to set
            value: Value to assign to the variable
        """
        self._prompt_vars[key] = str(value)
        # Immediately update prompt if in this FSM
        if self._app_ref.current_fsm is self:
            self._app_ref.prompt_manager.update_vars(self._prompt_vars)

    def clear_prompt_vars(self) -> None:
        """Clear all prompt formatting variables."""
        self._prompt_vars.clear()
        if self._app_ref.current_fsm is self:
            self._app_ref.prompt_manager.update_vars({})

    # hooks
    async def on_fsm_enter(self) -> None:
        """Called when FSM session starts (after initial state enter)."""
        pass

    async def on_fsm_exit(self) -> None:
        """Called when FSM session ends (before cleanup)."""
        pass
