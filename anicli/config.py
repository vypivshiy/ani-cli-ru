from prompt_toolkit.shortcuts import CompleteStyle

from anicli.core import CliApp

app: CliApp = CliApp(complete_style=CompleteStyle.MULTI_COLUMN)
