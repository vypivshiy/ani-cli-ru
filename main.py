from __future__ import annotations
import subprocess
import datetime
import os
from random import sample
from string import hexdigits

from prompt_toolkit.validation import Validator
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import set_title

from anicli.cli import CliApp

# TODO change default print to print_formatted_text

def get_prompt():
    now = datetime.datetime.now()
    now_time = f"{now.hour:02}:{now.minute:02}:{now.second:02}"
    set_title(f"Demo Cli app {now_time}")
    rand_color = "#" + "".join([sample(hexdigits, 1)[0] for _ in range(6)])
    return [
        (rand_color, f"[{os.getlogin()}] "),
        ("bg:#008800 #ffffff", f" {now.hour:02}:{now.minute:02}:{now.second:02}"),
        ("", " *_~ ")
    ]

_default_style = Style.from_dict(
    {        # Default style.
        "": "#0031ff bold",
        # Prompt.
        "prompt": "#ffd966 italic",
        # Make a selection reverse/underlined.
        # (Use Control-Space to select.)
        "selected-text": "reverse underline",
        "completer": "#f1c232"}
)

app = CliApp(message=get_prompt, refresh_interval=0.5, style=_default_style)

# this command never added
@app.command(["help"])
def _help():
    print("not set")


@app.command(["echo"], help_meta="print all passed arguments")
def echo(*args):
    print(args)

def ping_rule(count: str, _: str):
    if not count.replace("-", "").isdigit():
        print("Error! count should be integer")
        return False
    if int(count) < 1:
        print("Error! count must be positive value")
        return False
    return True

@app.command(["ping"], help_meta="send PING packets",
             rule=ping_rule)
def ping(count, domain):
    subprocess.run(["ping", f"-c {count}", domain])


@app.command(["sum"], help_meta="output sum arguments")
def sum_(*digits: int):
    print(" + ".join([str(d) for d in digits]), "=", sum(digits))


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
        try:
            text = session.prompt(f"[sum {result}] > ",
                                  bottom_toolbar=f"result={result}")
            result += int(text)
        except (KeyboardInterrupt, EOFError):
            print("RESULT", result, "exit")
            return


@app.command(["text-upper"], "set text in upper case",
             args_hook=lambda *args: (" ".join(args),))
def upper(text: str):
    print(text.upper())


if __name__ == '__main__':
    app.run(debug=True)
