from typing import Any, Dict, List, Sequence, Tuple

from prompt_toolkit.completion import WordCompleter

_ASSIGNED_COMMANDS = ("..", "~")
_ASSIGNED_COMMANDS_META = {"..": "back to prev step", "~": "back to main menu"}
_ASSIGNED_COMMANDS_EPISODES = ("..", "~", "info")
_ASSIGNED_COMMANDS_EPISODES_META = {
    "..": "back to prev step",
    "~": "back to main menu",
    "info": "show full description",
}

_WORDS_T = List[str]
_META_WORDS_T = Dict[str, str]


def _parse_items_completion(items_list: Sequence[Any]) -> Tuple[_WORDS_T, _META_WORDS_T]:
    return (
        [str(i + 1) for i in range(len(items_list))],  # words
        {str(i + 1): str(item) for i, item in enumerate(items_list)},
    )  # meta


def word_choice_completer(items_list: Sequence[Any]):
    commands = _ASSIGNED_COMMANDS
    commands_meta = _ASSIGNED_COMMANDS_META
    words, meta_dict = _parse_items_completion(items_list)

    words.extend(commands)
    meta_dict.update(commands_meta)
    return WordCompleter(words=words, meta_dict=meta_dict)


def anime_word_choice_completer(items_list: Sequence[Any]):
    commands = _ASSIGNED_COMMANDS_EPISODES
    commands_meta = _ASSIGNED_COMMANDS_EPISODES_META
    words, meta_dict = _parse_items_completion(items_list)

    words.extend(commands)
    meta_dict.update(commands_meta)
    return WordCompleter(words=words, meta_dict=meta_dict)
