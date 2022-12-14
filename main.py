from __future__ import annotations
import subprocess

from prompt_toolkit.filters import Condition
from prompt_toolkit.validation import Validator

from anicli.cli import CliApp

app = CliApp()

# rewrite default command
app.remove_command("exit")


# this command never added
@app.command(["help"])
def _help(_):
    print("not set")


@app.command(["exit", "quit"], "exit this app")
def _exit(_):
    text = app.session.prompt("exit? (y/n)")
    if text == "y":
        exit(1)
    return


@app.command(["echo"], help_meta="print all passed arguments")
def echo(command, *args):
    print(command, args)


@app.command(["ping"], help_meta="send PING packets")
def ping(_, count, domain):
    subprocess.run(["ping", f"-c {count}", domain])


@app.command(["sum"], help_meta="output sum arguments")
def sum_(_, *digits: int):
    print(" + ".join([str(d) for d in digits]), "=", sum(digits))


@app.command(["sum-interactive"], help_meta="interactive sum")
def sum_interactive(_):
    print("Press ctrl+c or ctrl+d for exit")
    result = 0
    validator = Validator.from_callable(lambda s: s.isdigit(),
                                        error_message="Is not digit",
                                        move_cursor_to_end=True)

    while True:
        try:
            text = app.session.prompt("[d] >",
                                      validator=validator,
                                      bottom_toolbar=f"result={result}",
                                      validate_while_typing=True)
            result += int(text)
        except (KeyboardInterrupt, EOFError):
            # todo auto clear session config
            app.session.validator = None
            app.session.validate_while_typing = False
            app.session.bottom_toolbar = None

            print("RESULT", result, "exit")
            return


if __name__ == '__main__':
    app.run(debug=True)
