"""config PromptSession and CliApp class"""

from random import choice
import datetime
import os
from string import hexdigits

from prompt_toolkit.shortcuts import set_title, CompleteStyle
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import ANSI
from anicli.core import CliApp, Dispatcher


def get_prompt():
    now = datetime.datetime.now()
    now_time = f"{now.hour:02}:{now.minute:02}:{now.second:02}"
    set_title(f"Demo Cli app {now_time}")
    rand_color = "#" + "".join([choice(hexdigits) for _ in range(6)])
    return [
        (rand_color, f"[{os.getlogin()}] "),
        ("bg:#008800 #ffffff", f" {now.hour:02}:{now.minute:02}:{now.second:02}"),
        ("", " *_~ ")
    ]


DEFAULT_STYLE = Style.from_dict(
    {   # Default style.
        "": "#0031ff bold",
        # Prompt.
        "prompt": "#ffd966 italic",
        # Make a selection reverse/underlined.
        # (Use Control-Space to select.)
        "selected-text": "reverse underline",
        "completer": "#f1c232"}
)

app = CliApp(message=get_prompt,
             refresh_interval=0.5,
             style=DEFAULT_STYLE,
             description=ANSI("\x1b[1mSAMPLE START DESCRIPTION\ntype help for get commands"),
             )

dp = Dispatcher(app)