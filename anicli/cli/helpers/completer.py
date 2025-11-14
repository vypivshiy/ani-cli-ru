"""Набор вспомогательных функций для создания комплитерев для всех команд поиска/проигрывания тайтлов"""

from typing import TYPE_CHECKING, Iterable, List, Tuple, Union

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseEpisode, BaseOngoing, BaseSearch, BaseSource


def make_ongoing_or_search_completer(
    results: Iterable[Union["BaseOngoing", "BaseSearch"]], current_text: str
) -> List[Tuple[str, str]]:
    # fi
    completions = [(str(i), result.title) for i, result in enumerate(results, 1)]
    if current_text:
        title_completions = []
        for i, result in enumerate(results, 1):
            if current_text.lower() in result.title.lower():
                # Add the title as a completion option with index as the actual value to submit
                title_completions.append((str(i), f"[#{i}] {result.title} "))
        # Insert title completions at the beginning
        completions = title_completions + completions

    return completions
