from typing import Any, List, Literal, Sequence, Union

from anicli.common.utils import is_arabic_digit

from .episode_picker import parse_selection_mask


def validate_prompt_index(results: Sequence[Any], user_input: str) -> Union[str, Literal[True]]:
    """return true if userinput is digit and its valid index in result

    index starts at 1
    """
    max_index = len(results)

    if is_arabic_digit(user_input):
        value = int(user_input)
        if value == 0:
            return "start index should be at 1"
        elif value > max_index:
            return f"out of range (max index {max_index})"
        return True
    return "choice matched title"
    # else:
    #     # Check if the input is a title match
    #     # Find if the input matches any title (case-insensitive)
    #     for _, result in enumerate(results, 1):
    #         if user_input.lower() in result.title.lower():
    #             # If there's a match, return True (valid)
    #             return True
    #     return f"should be a number in range (1-{max_index}) or a title that matches one of the results"


def validate_prompt_episode(results: Union[Sequence[Any], List[Any]], user_input: str) -> Union[str, Literal[True]]:
    if user_input == "":
        return "episode index or slice required"
    try:
        _mask = parse_selection_mask(user_input, len(results))
        return True
    except ValueError as e:
        return e.args[0]
