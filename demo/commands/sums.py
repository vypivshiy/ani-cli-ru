from prompt_toolkit.validation import Validator

from anicli.core import BaseDispatcher
from demo.config import app


@app.command(["sum"], help_meta="output sum arguments")
def sum_(*digits: int):
    print(" + ".join([str(d) for d in digits]), "=", sum(digits))


@app.on_command_error()
def sum_(ctx: app, error: Exception, *args):
    if isinstance(error, ValueError):
        print("Error!", *args, "is not integers")


@app.command(["sum-interactive"], help_meta="interactive sum")
def sum_interactive():
    print("Press ctrl+c or ctrl+d for exit")
    result = 0
    validator = Validator.from_callable(lambda s: s.isdigit(),
                                        error_message="Is not digit",
                                        move_cursor_to_end=True)
    session = app.new_prompt_session(f"[sum {result}] > ",
                                     validator=validator,
                                     bottom_toolbar=f"result={result}",
                                     validate_while_typing=True)
    while True:
        text = session.prompt(f"[sum {result}] > ",
                              bottom_toolbar=f"result={result}")
        result += int(text)


@app.on_command_error()
def sum_interactive(ctx: BaseDispatcher, error: Exception):
    if isinstance(error, KeyboardInterrupt):
        print("KeyboardInterrupt, Exit")
    elif isinstance(error, EOFError):
        print("EOFError, Exit")
    return
