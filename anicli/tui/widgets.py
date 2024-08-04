from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.validation import Number
from textual.widgets import ListItem, Label, Static, ListView, Button, Input

from anicli2.tui.consts import LOGO_HEADER
from .validators import InputPeekValidator
from ..types_ import ANICLI_API_ITEM
from ..utils.more_itertools import chunked


class ListPaginator(Static):
    """paginator component"""
    DEFAULT_CSS = """
        #prev-page {
            width: 1;
            margin: 1;
        }
        #next-page {
            width: 1;
            margin: 1;
        }
        #pager-goto-input{
            width: 10;
            margin: 1;
        }
        #pager-goto-button{
            width: 3;
            margin: 1;
        }
        #pager-container{
            align: center top;
        }
        #pager-content-container{
            height: 50%;
        }
        #pager-goto-choice {
            width: 30;
            margin: 1;
        }
    """

    def __init__(self, *items: ListItem, stack=50, start_index=0, id: str):
        # TODO: provide any default kwargs
        super().__init__(id=id)

        _x, _y = divmod(len(items), stack)
        self.max_pages = _x if _y == 0 else _x + 1
        self.items = list(items)

        self.chunks_items = list(chunked(items, stack))

        self.cur_index = start_index
        self.end_index = len(self.chunks_items) - 1
        self.validator_num = Number(
            minimum=1,
            maximum=self.max_pages,
            failure_description=f'should be in range 1-{self.max_pages}'
        )

    @property
    def current_page(self):
        return self.cur_index + 1

    def next_page(self):
        self.cur_index += 1

    def prev_page(self):
        self.cur_index -= 1

    def compose(self) -> ComposeResult:
        # show slice indexes
        with Vertical(id='pager-content-container'):
            yield Label(f'Page 1/1 | items: {len(self.items)}', id='pager-counter')
            yield ListView(*self.chunks_items[self.cur_index], id='list-pager')

        with Horizontal(id='pager-container'):
            yield Button('<', id='prev-page')
            yield Input(placeholder='goto',
                        validators=self.validator_num,
                        id='pager-goto-input',
                        max_length=3)
            yield Button('>', id='next-page')

    def on_mount(self):
        # not need pagination
        self.query_one('#pager-counter', Label).update(f'Page 1/{self.max_pages} | items: {len(self.items)}')
        self._update_buttons_states()

    @on(Button.Pressed, '#prev-page')
    def prev_page_click(self, _):
        self.prev_page()

        self._update_buttons_states()
        self._update_listview()

        self.query_one('#pager-counter', Label).update(f'Page {self.current_page}/{self.max_pages}')

    @on(Button.Pressed, '#next-page')
    def next_page_click(self, _):
        self.next_page()

        self._update_buttons_states()
        self._update_listview()

        self.query_one('#pager-counter', Label).update(f'Page {self.current_page}/{self.max_pages} | items: {len(self.items)}')

    @on(Input.Submitted, '#pager-goto-input')
    def jump_page_input(self, event: Input.Submitted):
        val = event.value
        if not val.isdigit() or val == '0' or int(val) > self.max_pages:
            return

        val = int(event.value)
        self.cur_index = val - 1

        self._update_buttons_states()
        self._update_listview()

        self.query_one('#pager-counter', Label).update(f'Page {self.current_page}/{self.max_pages} | items: {len(self.items)}')

    def _update_listview(self):
        items_slice = self.chunks_items[self.cur_index]
        lst = self.query_one('#list-pager', ListView)
        lst.clear()

        lst.extend(items_slice)

    def _update_buttons_states(self):
        if self.max_pages == 1:
            self._on__disable_buttons()
        elif self.current_page == 1:
            self._on__disable_prev_button()
        elif self.current_page == self.max_pages:
            self._on__disable_next_button()
        else:
            self._on__activate_buttons()

    def _on__activate_buttons(self):
        b1 = self.query_one('#prev-page', Button)
        b1.disabled = False
        b2 = self.query_one('#next-page', Button)
        b2.disabled = False

    def _on__disable_next_button(self):
        self.query_one('#prev-page', Button).disabled = False
        self.query_one('#next-page', Button).disabled = True

    def _on__disable_prev_button(self):
        self.query_one('#prev-page', Button).disabled = True
        self.query_one('#next-page', Button).disabled = False

    def _on__disable_buttons(self):
        self.query_one('#prev-page', Button).disabled = True
        self.query_one('#next-page', Button).disabled = True
        self.query_one('#pager-goto-input').disabled = True


class AnimeListItem(ListItem):
    """modified ListItem helps storage iterable anicli-api objects"""

    def __init__(self, num: int, item: ANICLI_API_ITEM):
        super().__init__()
        self.num = num
        self._item = item

    @property
    def value(self):
        return self._item

    def compose(self) -> ComposeResult:
        yield Label(f'{self.num}) {self._item}')


class AppHeader(Horizontal):
    LOGO = LOGO_HEADER
    STATIC_TITLE: str = 'Anicli-ru'
    COLLAPSED: bool = True

    def compose(self):
        yield Static(self.LOGO)
