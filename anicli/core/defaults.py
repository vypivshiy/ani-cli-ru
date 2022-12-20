from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText

ERROR_STYLE = Style.from_dict({"error": "red"})
ERROR_FRAGMENT = FormattedText([("class:error", "ERROR ")])
