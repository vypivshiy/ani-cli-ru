import subprocess

from prompt_toolkit.completion import NestedCompleter

from anicli.core import BaseDispatcher
from demo.config import app


@app.command(["echo"], help_meta="print all passed arguments")
def echo(*args):
    print(args)


def ping_rule(count: str, _command: str):
    if not count.replace("-", "").isdigit():
        print("Error! count should be integer")
        return False
    if int(count) < 1:
        print("Error! count must be positive value")
        return False
    return True


@app.command(["ping"], rule=ping_rule)
def ping(count, domain):
    """DOCSTRING send PING packets"""
    subprocess.run(["ping", f"-c {count}", domain])


@app.command("zsh")
def zsh():
    """open zsh shell"""
    subprocess.run("zsh")


@app.on_command_error()
def zsh(ctx, error: Exception):
    if isinstance(error, FileNotFoundError):
        print("not found zsh, run bash")
        app.command_handler("bash")


@app.command("bash")
def bash():
    """open bash shell"""
    subprocess.run("bash")


@app.on_command_error()
def bash(ctx: BaseDispatcher, error):
    if isinstance(error, FileNotFoundError):
        print("not found bash. input available shell")
        text = ctx.session.prompt("> ")
        try:
            subprocess.run(text)
        except FileNotFoundError:
            print("error, return to main")
