from typing import List, Any, Dict, Tuple

from prompt_toolkit.completion import WordCompleter


def _parse_items_completion(items_list: List[Any]) -> Tuple[List[str], Dict[str, str]]:
    return [str(i) for i in range(len(items_list))], {str(i): str(item) for i, item in enumerate(items_list)}


def word_completer(items_list: List[Any]):
    commands = ["..", "~"]
    commands_meta = {"..": "back to prev step", "~": "back to main menu"}
    words, meta_dict = _parse_items_completion(items_list)

    words.extend(commands)
    meta_dict.update(commands_meta)
    return WordCompleter(words=words,
                         meta_dict=meta_dict)


def anime_word_completer(items_list: List[Any]):
    commands = ["..", "~", "info"]
    commands_meta = {"..": "back to prev step", "~": "back to main menu", "info": "show full description"}
    words, meta_dict = _parse_items_completion(items_list)

    words.extend(commands)
    meta_dict.update(commands_meta)
    return WordCompleter(words=words,
                         meta_dict=meta_dict)