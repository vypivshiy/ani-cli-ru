"""A sidebar screen widget. should be works only in main page"""
# TODO wrap functional to this screen

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Button, RadioButton, RadioSet, Collapsible, Input

from anicli.utils.fetch_extractors import get_extractor_modules


class Sidebar(VerticalScroll):
    AVAILABLE_EXTRACTORS = get_extractor_modules()
    QUALITIES = [1080, 720, 480, 360, 'manual']

    def on_mount(self):
        self.query_one('#sidebar-source').tooltip = 'choice source provider for extract video'
        self.query_one('#sidebar-quality').tooltip = '''set prefered video qualities. 

NOTE: If the selected resolution is not available in the found video, it will select another available one:
1080 > 720 > 480 > 360

in manual mode you have to choose it yourself
        '''
        self.query_one('#sidebar-proxy').tooltip = '''set proxy for next requests

WARNING: most extractors supports only CIS and Baltics regions
        '''

    def compose(self) -> ComposeResult:
        with Collapsible(title='Source'):
            yield RadioSet(
                *[RadioButton(name, i) for i, name in enumerate(self.AVAILABLE_EXTRACTORS)],
                id='sidebar-source'
            )
        with Collapsible(title='Quality'):
            yield RadioSet(
                *[RadioButton(str(quality), quality) for quality in self.QUALITIES],
                id='sidebar-quality'
            )
        with Collapsible(title='Network'):
            yield Input(placeholder='Proxy', id='sidebar-proxy')
            yield Button('TEST')
        yield Button('Apply', variant='success', id='sidebar-success')
