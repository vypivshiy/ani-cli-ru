from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator

from anicli.core import BaseState
from demo.config import dp


class State(BaseState):
    FIRST_NAME = 1
    LAST_NAME = 2
    AGE = 3
    HOBBIES = 4


@dp.command("fsm-example")
def start_fsm():
    """mini FSM questionnaire example"""
    print("ENTER TO FSM STATE EXAMPLE")
    dp.state_dispenser.set(State.FIRST_NAME)


@dp.state_handler(State.FIRST_NAME)
def state_1():
    first_name = prompt("Enter your first name > ")
    dp.state_dispenser.update({"first_name": first_name})
    dp.state_dispenser.set(State.LAST_NAME)

@dp.state_handler(State.LAST_NAME)
def state_2():
    last_name = prompt("Enter your last name > ")
    dp.state_dispenser.update({"last_name": last_name})
    dp.state_dispenser.set(State.AGE)


@dp.state_handler(State.AGE)
def state_3():
    age = prompt("Enter your age > ", validator=Validator.from_callable(lambda s: s.isdigit(),
                                                                        error_message="Is not positive integer"))
    dp.state_dispenser.update({"age": int(age)})
    dp.state_dispenser.set(State.HOBBIES)


@dp.state_handler(State.HOBBIES)
def state_4():
    hobbies = prompt("Enter your hobbies > ")
    dp.state_dispenser.update({"hobbies": hobbies})
    print("Your inputs: ")
    print(*[f"{k} {v}" for k,v in dp.state_dispenser.storage.items()], sep="\n")
    # !!!! DON'T FORGET TO CLOSE THE FSM
    dp.state_dispenser.finish()