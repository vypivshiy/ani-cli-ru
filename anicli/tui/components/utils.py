from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.widget import Widget

from contextlib import contextmanager


@contextmanager
def start_loading(element: 'Widget'):
    """helper context manager that starts loading element state"""
    try:
        element.loading = True
        yield element
    finally:
        element.loading = False
