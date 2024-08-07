from typing import Any, List

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.events import Mount
from textual.widgets import SelectionList, Static, Button, Input, TextArea
from textual.widgets.selection_list import Selection

from anicli.tui.components.utils import set_loading
from anicli.tui.validators import NumberPeekValidator


class EpisodesSelector(Static):
    def __init__(self, lst_items: List[Any], id: str):
        super().__init__(id=id)
        self._items = lst_items
        self._len = len(lst_items)
        self.validator = NumberPeekValidator(self._items)

    def on_mount(self):
        self.query_one('#episodes-items', SelectionList).border_title = \
            'Choice Episodes'
        self.query_one('#episodes-selected-textbox', TextArea).border_title = \
            'Episodes picked'
        self.query_one('#episodes-picker-input', Input).tooltip = \
            'accept digits "5", slice "1-3", sequence "1 2 3"'

    def _selected_args(self):
        for i, item in enumerate(self._items):
            yield Selection(str(item), i)

    def compose(self) -> ComposeResult:
        yield SelectionList(*self._selected_args(),
                            id='episodes-items')
        with Horizontal(id='episodes-selector-container'):
            yield Input(placeholder='Select',
                        id='episodes-picker-input',
                        validators=self.validator)
            yield Button('All', id='episodes-pick-all')
            yield Button('Clear', id='episodes-pick-clear', variant="error")
            yield Button('Next', id='episodes-pick-accept', variant='success')

        yield TextArea(read_only=True, id='episodes-selected-textbox')

    def _selected_items_to_list_items(self) -> str:
        sel = self.query_one('#episodes-items', SelectionList).selected
        return '\n'.join(f'{i + 1}) {self._items[i]}' for i in sel)

    @on(Input.Submitted, '#episodes-picker-input')
    def pick_from_input(self, ev: Input.Submitted):
        result = self.validator.parse(ev.value)
        if not result and result != 0:
            self.notify('Wrong picker format', severity='error')
            return
        ev.input.loading = True
        with set_loading(ev.input):
            selection_list = self.query_one('#episodes-items', SelectionList)
            if isinstance(result, int):
                selection_list.select(result)
            elif isinstance(result, range):
                for i in result:
                    selection_list.select(i)
            elif isinstance(result, list):
                for i in result:
                    selection_list.select(i)
            else:
                self.notify(f'something wrong: input: {ev.value}, result: {result}')

    @on(Button.Pressed, '#episodes-pick-all')
    def pick_all_selected_items(self, ev: Button.Pressed):
        with set_loading(ev.button):
            self.query_one('#episodes-items', SelectionList).select_all()

    @on(Button.Pressed, '#episodes-pick-clear')
    def clear_all_selected_items(self, ev: Button.Pressed):
        with set_loading(ev.button):
            self.query_one('#episodes-items', SelectionList).deselect_all()

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    def _update_selected_view(self):
        self.query_one('#episodes-selected-textbox').loading = True
        with set_loading(self.query_one('#episodes-selected-textbox')):
            if not self.query_one('#episodes-items', SelectionList).selected:
                self.query_one('#episodes-selected-textbox', TextArea).clear()
                self.query_one('#episodes-selected-textbox', TextArea).border_title = 'Episodes picked'
                return

            self.query_one('#episodes-selected-textbox', TextArea).text = self._selected_items_to_list_items()
            count = len(self.query_one('#episodes-items', SelectionList).selected)
            self.query_one('#episodes-selected-textbox', TextArea).border_title = f'Episodes picked: {count}'

