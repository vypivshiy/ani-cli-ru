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
    """Global application context with generic type support"""

    app: "Application[CtxT]"
    _data: CtxT

    @property
    def data(self) -> CtxT:
        return self._data


@dataclass
class CommandContext(Generic[CtxT]):
    """Context passed to command handlers"""

    app: "Application"
    command: "CommandRoute"
    args: str  # raw args string
    _data: CtxT

    @property
    def data(self) -> CtxT:
        return self._data


@dataclass
class FSMContext(Generic[CtxT]):
    """Context for a single FSM session."""

    app: "Application"
    state_history: List[str]
    current_state: Optional["FSMState"]
    _data: CtxT

    @property
    def route_key(self) -> Optional[str]:
        if self.current_state:
            return self.current_state.name
        return None

    @property
    def data(self) -> CtxT:
        return self._data


T_VALIDATOR = Union[Callable[[Any, CommandContext], bool], Validator]
T_FSM_VALIDATOR = Callable[[str, FSMContext], bool]


@dataclass
class CommandRoute:
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
        return self.handler(*args, **kwargs)


@dataclass
class FSMState:
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
        return self.handler(*args, **kwargs)


@dataclass
class FSMRoute:
    key: str
    help: str
    fsm_class: Type["BaseFSM"]
    states: Dict[str, FSMState]
    initial_state: str
    middleware: List[Callable] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    _current_state: Optional[FSMState] = None

    def __call__(self, *args, **kwargs):
        return self.fsm_class(*args, **kwargs)

    def set_state(self, key: str) -> None:
        self._current_state = self.states[key]

    @property
    def current_state(self) -> Optional[FSMState]:
        # Return the currently active state if set, otherwise None
        return self._current_state


@dataclass
class ErrorHandler:
    """Error handler configuration"""

    exception_type: type
    handler: Callable[[Exception, str], Optional[str]]

    def __call__(self, *args, **kwargs) -> Optional[str]:
        return self.handler(*args, **kwargs)
