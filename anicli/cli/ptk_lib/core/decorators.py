"""High-level decorators API for commands and FSMs"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from prompt_toolkit.completion import Completer, WordCompleter

from .completer import NestedCompleterWithMeta
from .fsm import BaseFSM
from .types import T_VALIDATOR, CommandRoute, FSMRoute, FSMState

_LEN_META_COMPLETER_ITEM = 2


def _create_completer_from_value(value: Any) -> Optional[Completer]:
    """
    Auto-create completer from various input types:
    - Completer -> use as-is
    - List[str] -> WordCompleter
    - List[Tuple[str, str]] -> WordCompleter with meta
    - Dict[str, Any] -> NestedCompleterWithMeta
        - key "_meta" - pass meta information
        - key "_completions" - pass word completer
    """
    if value is None:
        return None

    # Already a Completer
    if isinstance(value, Completer):
        return value

    # Dict -> NestedCompleterWithMeta
    if isinstance(value, dict):
        return NestedCompleterWithMeta.from_nested_dict(value)

    # List -> check first element type
    if isinstance(value, (list, tuple)) and len(value) > 0:
        first = value[0]

        # List[Tuple[str, str]] -> WordCompleter with meta_dict
        if isinstance(first, (tuple, list)) and len(first) >= _LEN_META_COMPLETER_ITEM:
            words = [item[0] for item in value]
            meta_dict = {item[0]: item[1] for item in value if len(item) >= _LEN_META_COMPLETER_ITEM}
            return WordCompleter(words, meta_dict=meta_dict, ignore_case=True)

        # List[str] -> WordCompleter
        elif isinstance(first, str):
            return WordCompleter(list(value), ignore_case=True)

    return None


def command(
    key: str,
    help: str = "",  # noqa: A002
    *,
    sub_commands: Optional[List[Union[Callable, "CommandRoute"]]] = None,
    validator: Optional[T_VALIDATOR] = None,
    middleware: Optional[List[Callable]] = None,
    aliases: Optional[List[str]] = None,
    parser: Optional[Callable[[str], Any]] = None,
    completer: Optional[Union[Completer, List[str], List[Tuple[str, str]], Dict[str, Any]]] = None,
    usage: Optional[str] = None,
    examples: Optional[List[str]] = None,
    arguments: Optional[Dict[str, str]] = None,
) -> Callable[..., CommandRoute]:
    def decorator(func: Callable) -> CommandRoute:
        # Process sub_commands - extract routes
        processed_sub_commands = []
        if sub_commands:
            for sc in sub_commands:
                if isinstance(sc, CommandRoute):
                    route = sc
                else:
                    msg = f"Invalid sub_command: {sc}. Must be CommandRoute or decorated function"
                    raise ValueError(msg)
                processed_sub_commands.append(route)

        # Auto-create completer from input value
        final_completer = _create_completer_from_value(completer)

        # Fallback to completer_tree for backward compatibility
        route = CommandRoute(
            key=key,
            help=help,
            handler=func,
            validator=validator,
            middleware=middleware or [],
            aliases=aliases or [],
            parser=parser,
            completer=final_completer,
            usage=usage,
            examples=examples or [],
            arguments=arguments or {},
            sub_commands=processed_sub_commands,
        )

        # Set parent reference for sub_commands
        for sub_cmd in processed_sub_commands:
            sub_cmd.parent = route
        return route

    return decorator


def fsm_route(
    key: str,
    help: str = "",  # noqa: A002
    *,
    middleware: Optional[List[Callable]] = None,
    aliases: Optional[List[str]] = None,
) -> Callable[..., FSMRoute]:
    """Decorator to register an FSM class.

    Returns FSMRoute (which wraps the class).
    """

    def decorator(cls: Type[BaseFSM]) -> FSMRoute:
        if not issubclass(cls, BaseFSM):
            msg = "FSM route class must inherit from BaseFSM"
            raise TypeError(msg)

        states = {}
        initial_state = None

        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, FSMState):
                states[attr.name] = attr
                if initial_state is None:
                    initial_state = attr.name

        if not states:
            msg = f"No FSM states found in {cls.__name__}"
            raise ValueError(msg)
        if initial_state is None:
            msg = "FSM must have at least one state"
            raise ValueError(msg)

        route = FSMRoute(
            key=key,
            help=help,
            fsm_class=cls,
            states=states,
            initial_state=initial_state,
            middleware=middleware or [],
            aliases=aliases or [],
        )
        return route

    return decorator


def fsm_state(
    name: str,
    help: str = "",  # noqa: A002
    *,
    validator: Optional[Callable] = None,
    completer: Optional[Union[Completer, List[str], List[Tuple[str, str]], Dict[str, Any]]] = None,
    middleware: Optional[List[Callable]] = None,
    on_enter: Optional[Callable] = None,
    on_exit: Optional[Callable] = None,
    prompt_message: Optional[str] = None,
) -> Callable[..., FSMState]:
    def decorator(func: Callable) -> FSMState:
        # Auto-create completer from input value
        final_completer = _create_completer_from_value(completer)

        fsm_state = FSMState(
            name=name,
            help=help,
            handler=func,
            validator=validator,
            completer=final_completer,
            middleware=middleware or [],
            on_enter=on_enter,
            on_exit=on_exit,
            prompt_message=prompt_message,
        )
        return fsm_state

    return decorator
