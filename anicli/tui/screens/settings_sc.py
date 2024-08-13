"""A sidebar screen widget. should be works only in main page"""
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widget import Widget
from textual.widgets import Button, RadioButton, RadioSet, Collapsible, Input, Pretty

from anicli.utils.fetch_extractors import get_extractor_modules, import_extractor
from ...utils import CachedItemAsyncContext, CachedExtractorAsync

if TYPE_CHECKING:
    pass
# TODO move to consts
_SIDEBAR_SOURCE = 'choice source provider for extract video'
_SIDEBAR_QUALITY = '''set prefered video qualities. 

NOTE: If the selected resolution is not available in the found video, it will select another available one:
1080 > 720 > 480 > 360

in manual mode you have to choose it yourself
'''

_SIDEBAR_PROXY = '''(TODO) set proxy for next requests

WARNING: most extractors supports only CIS and Baltics regions
'''


class Sidebar(VerticalScroll):
    AVAILABLE_EXTRACTORS = get_extractor_modules()
    QUALITIES = [1080, 720, 480, 360, 0]

    def __init__(self,
                 *children: Widget,
                 classes: str,
                 id: str):
        super().__init__(*children, classes=classes, id=id)

        # TODO: TypedDict typing
        self.picked_settings = {}

    def on_mount(self):
        self.query_one('#sidebar-source').tooltip = _SIDEBAR_SOURCE
        self.query_one('#sidebar-quality').tooltip = _SIDEBAR_QUALITY
        self.query_one('#sidebar-proxy').tooltip = _SIDEBAR_PROXY

    def compose(self) -> ComposeResult:
        with Collapsible(title='Source'):
            yield RadioSet(
                *[RadioButton(name) for name in self.AVAILABLE_EXTRACTORS],
                id='sidebar-source'
            )
        with Collapsible(title='Quality'):
            yield RadioSet(
                *[RadioButton(str(quality)) for quality in self.QUALITIES],
                id='sidebar-quality'
            )
        with Collapsible(title='Network'):
            yield Input(placeholder='Proxy', id='sidebar-proxy', disabled=True)
            yield Button('TEST', disabled=True)
        with Collapsible(title='chosen options:', collapsed=False):
            yield Pretty(self.picked_settings, id='sidebar-options')
        with Horizontal():
            yield Button('Apply', variant='success', id='sidebar-success')
            yield Button('Reset', id='sidebar-reset')

    @on(RadioSet.Changed, '#sidebar-source')
    async def pick_source(self, event: RadioSet.Changed) -> None:
        self.picked_settings['extractor'] = event.pressed.label.plain

        self.query_one('#sidebar-options', Pretty).update(self.picked_settings)

    @on(RadioSet.Changed, '#sidebar-quality')
    async def pick_quality(self, event: RadioSet.Changed) -> None:
        self.picked_settings['quality'] = int(event.pressed.label.plain)

        self.query_one('#sidebar-options', Pretty).update(self.picked_settings)

    @on(Button.Pressed, '#sidebar-reset')
    async def reset(self) -> None:
        self.picked_settings.clear()

        self.query_one('#sidebar-options', Pretty).update({})
