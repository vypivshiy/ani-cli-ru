"""Набор вспомогательных функций для создания комплитерев для всех команд поиска/проигрывания тайтлов"""

from typing import TYPE_CHECKING, Iterable, List, Tuple, Union

if TYPE_CHECKING:
    from anicli_api.base import BaseOngoing, BaseSearch


def make_ongoing_or_search_completer(
    results: Iterable[Union["BaseOngoing", "BaseSearch"]], current_text: str
) -> List[Tuple[str, str]]:
    # Optimization: One-pass iteration and pre-calculate search term
    search_term = current_text.lower() if current_text else None

    title_matches = []
    all_indices = []

    for i, result in enumerate(results, 1):
        idx_str = str(i)
        title = result.title

        all_indices.append((idx_str, title))

        if search_term and (search_term == idx_str or search_term in title.lower()):
            title_matches.append((idx_str, f"[#{idx_str}] {title} "))

    # Return prioritized matches followed by the full list
    return title_matches + all_indices
