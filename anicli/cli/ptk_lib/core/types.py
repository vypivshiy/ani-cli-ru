"""Core type definitions and data structures"""

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
)

from prompt_toolkit.completion import Completer
from prompt_toolkit.validation import Validator

if TYPE_CHECKING:
    from .application import Application
    from .fsm import BaseFSM


T = TypeVar("T")
CtxT = TypeVar("CtxT", bound=Union[Dict[str, Any], Mapping[str, Any]])


@dataclass
class AppContext(Generic[CtxT]):
    """Global application context with generic type support.

    Args:
        app: Reference to the main Application instance
        _data: Generic data container for application context
    """

    app: "Application[CtxT]"
    _data: CtxT

    @property
    def data(self) -> CtxT:
        """Get the context data."""
        return self._data


@dataclass
class CommandContext(Generic[CtxT]):
    """Context passed to command handlers.

    Args:
        app: Reference to the main Application instance
        command: The CommandRoute being executed
        args: Raw arguments string passed to the command
        _data: Generic data container for command context
    """

    app: "Application"
    command: "CommandRoute"
    args: str  # raw args string
    _data: CtxT

    @property
    def data(self) -> CtxT:
        """Get the context data."""
        return self._data


@dataclass
class FSMContext(Generic[CtxT]):
    """Context for a single FSM session.

    Args:
        app: Reference to the main Application instance
        state_history: List of previous states in the FSM session
        current_state: The current FSM state, if any
        _data: Generic data container for FSM context
    """

    app: "Application"
    state_history: List[str]
    current_state: Optional["FSMState"]
    _data: CtxT

    @property
    def route_key(self) -> Optional[str]:
        """Get the current state name if a state is active."""
        if self.current_state:
            return self.current_state.name
        return None

    @property
    def data(self) -> CtxT:
        """Get the context data."""
        return self._data


T_VALIDATOR = Union[Callable[[Any, CommandContext], bool], Validator]
T_FSM_VALIDATOR = Callable[[str, FSMContext], bool]


@dataclass
class CommandRoute:
    """Definition of a command route with all its properties and configurations.

    Args:
        key: Unique identifier for the command
        help: Help text displayed for the command
        handler: Function that handles the command execution
        validator: Optional input validator for the command
        middleware: List of middleware functions to apply
        aliases: List of alternative names for the command
        parser: Optional function to parse command arguments
        completer: Optional completer for command arguments
        usage: Optional usage string for the command
        examples: List of example usages
        arguments: Dictionary of argument descriptions
        sub_commands: List of sub-commands for this command
        parent: Reference to parent command if this is a sub-command
    """

    key: str
    help: str
    handler: Callable
    validator: Optional[T_VALIDATOR] = None
    middleware: List[Callable] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    parser: Optional[Callable[[str], Any]] = None
    completer: Optional[Completer] = None
    usage: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    arguments: Dict[str, str] = field(default_factory=dict)

    sub_commands: List["CommandRoute"] = field(default_factory=list)
    parent: Optional["CommandRoute"] = field(default=None, repr=False)

    def __call__(self, *args, **kwargs):
        """Execute the command handler with given arguments."""
        return self.handler(*args, **kwargs)


@dataclass
class FSMState:
    """Definition of an FSM state with all its properties and configurations.

    Args:
        name: Unique name for the FSM state
        help: Help text displayed for the state
        handler: Function that handles the state execution
        validator: Optional input validator for the state
        completer: Optional completer for state input
        middleware: List of middleware functions to apply
        on_enter: Optional callback when entering the state
        on_exit: Optional callback when exiting the state
        prompt_message: Optional custom prompt message for the state
    """

    name: str
    help: str
    handler: Callable
    validator: Optional[T_FSM_VALIDATOR] = None
    completer: Optional[Completer] = None
    middleware: List[Callable] = field(default_factory=list)
    on_enter: Optional[Callable] = None
    on_exit: Optional[Callable] = None
    prompt_message: Optional[str] = None

    def __call__(self, *args, **kwargs):
        """Execute the state handler with given arguments."""
        return self.handler(*args, **kwargs)


@dataclass
class FSMRoute:
    """Definition of an FSM route with all its properties and configurations.

    Args:
        key: Unique identifier for the FSM route
        help: Help text displayed for the FSM
        fsm_class: The FSM class type that implements the route
        states: Dictionary of states available in the FSM
        initial_state: Name of the initial state to start the FSM
        middleware: List of middleware functions to apply
        aliases: List of alternative names for the FSM
        _current_state: The currently active state in the FSM session
    """

    key: str
    help: str
    fsm_class: Type["BaseFSM"]
    states: Dict[str, FSMState]
    initial_state: str
    middleware: List[Callable] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    _current_state: Optional[FSMState] = None

    def __call__(self, *args, **kwargs):
        """Instantiate the FSM class with given arguments."""
        return self.fsm_class(*args, **kwargs)

    def set_state(self, key: str) -> None:
        """Set the current active state in the FSM route.

        Args:
            key: The key of the state to set as current
        """
        self._current_state = self.states[key]

    @property
    def current_state(self) -> Optional[FSMState]:
        """Get the currently active state if set, otherwise None."""
        # Return the currently active state if set, otherwise None
        return self._current_state


@dataclass
class ErrorHandler:
    """Error handler configuration.

    Args:
        exception_type: The type of exception this handler manages
        handler: Function that handles the exception and returns an optional message
    """

    exception_type: type
    handler: Callable[[Exception, str], Optional[str]]

    def __call__(self, *args, **kwargs) -> Optional[str]:
        """Call the error handler with given arguments."""
        return self.handler(*args, **kwargs)
