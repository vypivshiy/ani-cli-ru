from prompt_toolkit.validation import Validator
from prompt_toolkit import PromptSession

from demo.config import dp


@dp.command(["add", "sum"])
def sum_(*digits: int):
    """output sum arguments"""
    print(" + ".join([str(d) for d in digits]), "=", sum(digits))


@sum_.on_error()
def sum_error(error: Exception, *args):
    if isinstance(error, ValueError):
        print("Error!", *args, "is not integers")
        return


@dp.command("sum-interactive", meta="interactive sum")
def sum_interactive():
    print("Press ctrl+c or ctrl+d for exit")
    result = 0
    validator = Validator.from_callable(lambda s: s.isdigit(),
                                        error_message="Is not digit",
                                        move_cursor_to_end=True)
    # need to create a new` PromptSession` class to avoid overwriting attrs settings
    session = PromptSession(f"[sum {result}] > ",
                                     validator=validator,
                                     bottom_toolbar=f"result={result}",
                                     validate_while_typing=True)
    while True:
        text = session.prompt(f"[sum {result}] > ",
                              bottom_toolbar=f"result={result}")
        result += int(text)


@sum_interactive.on_error()
def sum_interactive_error(error: Exception):
    if isinstance(error, KeyboardInterrupt):
        print("KeyboardInterrupt, Exit")
    elif isinstance(error, EOFError):
        print("EOFError, Exit")
    return
