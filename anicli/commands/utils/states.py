from anicli.config import dp
from anicli.core import BaseState


def on_exit_state(exc: BaseException):
    if isinstance(exc, (KeyboardInterrupt, EOFError)):
        print("KeyboardInterrupt, exit FROM State")
        dp.state_dispenser.finish()


def state_back(command: str, new_state: BaseState):
    if command == "..":
        dp.state_dispenser.set(new_state)
        return True
    return False


def state_main_loop(command: str):
    if command == "~":
        dp.state_dispenser.finish()
        return True
    return False


STATE_BACK = state_back
STATE_MAIN_LOOP = state_main_loop
