import subprocess

from demo.config import dp

# for add description in completer usage `meta` parameter or pass in docstrings
@dp.on_command(["echo", "duplicate"], meta="print all passed arguments")
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


# may not be typed.
@dp.on_command("ping", rule=ping_rule)
def ping(count, domain):
    """DOCSTRING send PING packets"""
    subprocess.run(["ping", f"-c {count}", domain])


@dp.on_command("bash")
def bash():
    """open bash shell"""
    subprocess.run("bash")


@bash.on_error()
def bash_error(error):
    if isinstance(error, FileNotFoundError):
        print("not found bash =(")
