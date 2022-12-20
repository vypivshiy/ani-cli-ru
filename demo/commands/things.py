from demo.config import app


# this command never added
@app.command(["help"])
def _help():
    print("not set")


@app.command(["text-upper"], "print input text to upper case",
             # join all arguments to one
             args_hook=lambda *args: (" ".join(args),))
def upper(text: str):
    print(text.upper())
