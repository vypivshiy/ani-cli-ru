"""commands for word completer"""
from anicli.config import dp
from anicli.core.states import BaseState

__all__ = (
    "BUILDIN_COMMANDS",
    "OPTIONAL_COMMANDS",
    "ON_ERROR_STATE",
    "ON_STATE_BACK",
    "ON_STATE_MAIN",
    "ON_STATE_PAGER",
)

BUILDIN_COMMANDS = {"..": "back to previous step", "~": "return to main REPL menu"}
OPTIONAL_COMMANDS = {"show": "Show detail information"}


def _on_error_state(exc: BaseException):
    if isinstance(exc, (KeyboardInterrupt, EOFError)):
        dp.state_dispenser.finish()
        return True
    raise exc


def _state_back(command: str, prev_state: BaseState) -> bool:
    if command == "..":
        dp.state_dispenser.set(prev_state)
        return True
    return False


def _state_return_main_loop(command: str) -> bool:
    if command == "~":
        dp.state_dispenser.finish()
        return True
    return False


def _state_pager_info(
    command: str, metadata: dict, prev_state: BaseState, info_state: BaseState
) -> bool:
    if command == "show":
        dp.state_dispenser["meta"] = metadata
        dp.state_dispenser["prev_state"] = prev_state
        dp.state_dispenser.set(info_state)
        return True
    return False


ON_ERROR_STATE = _on_error_state
ON_STATE_BACK = _state_back
ON_STATE_MAIN = _state_return_main_loop
ON_STATE_PAGER = _state_pager_info
