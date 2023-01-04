from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

ERROR_STYLE = Style.from_dict({"error": "red"})
ERROR_FRAGMENT = FormattedText([("class:error", "ERROR ")])
