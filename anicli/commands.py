from functools import partial
from prompt_toolkit.validation import Validator

from anicli_api.extractors import animego

from anicli.config import app


EXTRACTOR = animego.Extractor()


def _validate_num(digit: str, max_len: int):
    return digit.isdigit() and 0 <= int(digit) < max_len


def _check_input(query: str):
    if query:
        return True
    print("Query is empty")
    return False


@app.command(["search", "find"], "search anime titles by query",
             args_hook=lambda *args: (" ".join(list(args)),),
             rule=_check_input)
def search(query: str):
    results = EXTRACTOR.search(query)
    if len(results) > 0:
        print(*[f"{i} {r.name}" for i, r in enumerate(results)], sep="\n")

        print("choose title")
        session = app.new_prompt_session("[SEARCH] >")
        validator_func = partial(_validate_num, max_len=len(results))
        validator = Validator.from_callable(validator_func, error_message=f"Should be integer and (0<=n<{len(results)})")
        num = session.prompt("> ", validator=validator)
        anime_info = results[int(num)].get_anime()
        print(*[f"{k} - {v}" for k,v in anime_info.dict().items()], sep="\n")
        episodes = anime_info.get_episodes()
        print(*[f"{i} - {e.num} {e.name}" for i, e in enumerate(episodes)], sep="\n")
        validator_func = partial(_validate_num, max_len=len(episodes))
        validator = Validator.from_callable(validator_func,
                                            error_message=f"Should be integer and (0<=n<{len(episodes)})")
        num = session.prompt("[EPISODE] > ", validator=validator)
        episode = episodes[int(num)]
        videos = episode.get_videos()
        print("videos:")
        print(*[v.url for v in videos], sep="\n")
    else:
        print("Not found")
