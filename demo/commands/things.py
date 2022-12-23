from __future__ import annotations
from prompt_toolkit.shortcuts.dialogs import message_dialog

from demo.config import dp

# this command never added and throw AttributeError
# if you need rewrite command invoke `dp.remove_command("help")` method
# @app.command(["help"])
# def _help():
#    print("not set")


@dp.command(["text-upper"], "print input text to upper case",
             # join all arguments to one
             args_hook=lambda *args: (" ".join(args),))
def upper(text: str):
    print(text.upper())


@dp.command("about")
def about():
    """render prompt_toolkit.shortcuts.dialogs.message_dialog"""
    message_dialog(title="anicli.core DEMO",
                   text="Демонстрация вывода прочих виджетов prompt-toolkit",
                   ok_text="я понял").run()


def message_dialog_hook(*text: tuple[str, ...]):
    return tuple(" ".join(text).split("|", maxsplit=3))


def message_dialog_rule(*text: str):
    if len(" ".join(text).split("|", maxsplit=3)):
        return True
    print("Error! Need separate by `|` symbol")
    print("Example: title test|okay good nice|lorem upsum dolor volor molor")


@dp.command("message-dialog",
            rule=message_dialog_rule,
            args_hook=message_dialog_hook)
def message(title: str, ok_text: str, text: str):
    """construct and render message dialog. split with `|` symbol"""
    # title test123|a b c|any_text
    message_dialog(title=title,
                   ok_text=ok_text,
                   text=" ".join(text)).run()