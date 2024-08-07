from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.widget import Widget
    from textual.widgets import ListView, ListItem

from contextlib import contextmanager


@contextmanager
def set_loading(*elements: 'Widget') -> None:
    """helper context manager that starts loading element state"""
    try:
        for el in elements:
            el.loading = True
        yield

    finally:
        for el in elements:
            el.loading = False


def update_list_view(list_view: 'ListView', *items: 'ListItem') -> 'ListView':
    """clear current list_view widget and set as items values"""
    list_view.clear()
    list_view.extend(items)
    return list_view
