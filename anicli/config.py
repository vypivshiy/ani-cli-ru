from prompt_toolkit.shortcuts import CompleteStyle

from anicli.core import CliApp, Dispatcher

app: CliApp = CliApp(message="~ ", complete_style=CompleteStyle.MULTI_COLUMN)
dp = Dispatcher(app)
