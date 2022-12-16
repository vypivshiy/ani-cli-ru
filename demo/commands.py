import subprocess

from prompt_toolkit.validation import Validator

from demo.config import app


@app.command(["test", "ttest"], "test command")
def t_command(*_):
    print("test123")


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
