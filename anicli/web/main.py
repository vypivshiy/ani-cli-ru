#  pkg install clang libxml2 libxslt python-lxml.
# pip install .[web]
from typing import TypeVar, Sequence
from urllib.parse import urlsplit

from flask import Flask, render_template, request

from ..types_ import TYPER_CONTEXT_OPTIONS
from ..utils.anicli_api_helpers import get_video_by_quality
from ..utils.cached_extractor import CachedExtractor, CachedItemContext
from ..utils.fetch_extractors import import_extractor

T = TypeVar('T')

app = Flask(__name__)
app.config['cli_args']: TYPER_CONTEXT_OPTIONS

# TODO: implement switch extractor in runtime
IS_EXTRACTOR_LOADED = False
# in main route load extractor
CONTEXT = CachedItemContext(extractor=None)  # type: ignore


def match_item_by_kwargs(items: Sequence[T], **kwargs) -> T:
    """base web application state logic: search and return first item matching"""
    for i in items:
        if all(getattr(i, k, None) == v for k, v in kwargs.items()):
            return i
    raise TypeError('Failed match item')


@app.get('/')
def main():
    global IS_EXTRACTOR_LOADED

    if not IS_EXTRACTOR_LOADED:
        _EXTRACTOR = CachedExtractor(
            import_extractor(
                app.config['cli_args']['source'])()
        )
        CONTEXT.extractor = _EXTRACTOR
        IS_EXTRACTOR_LOADED = True

    modules = ['TODO: switch source']  # get_extractor_modules()

    # RESET ALL STATES
    CONTEXT.clear()

    ongoings_results = CONTEXT.ongoing()
    ongoings_element = render_template('ongoings_block.j2', ongoings_results=ongoings_results)
    select_providers = render_template('extractor_providers_block.j2', modules=modules)

    return render_template('index.j2',
                           select_providers=select_providers,
                           ongoings=ongoings_element
                           )


@app.get('/search')
def search():
    # TODO: validate input
    query = request.args.get('query', '')

    searches = CONTEXT.search(query)
    return render_template('search.j2', search_results=searches, title=f"Search {query}")


@app.post('/anime')
def anime_page():
    title = request.form['title']
    url = request.form['url']

    # HACK: get search/ongoing from cache by title and url
    match_item = match_item_by_kwargs(
        CONTEXT.searches_or_ongoings,
        url=url,
        title=title)
    anime = CONTEXT.get_anime(match_item)
    episodes = CONTEXT.get_episodes()
    return render_template('anime.j2', title=anime.title, episodes=episodes, anime=anime)


@app.get('/get_sources')
def anime_sources():
    num = request.args.get('num').strip()

    ep = match_item_by_kwargs(CONTEXT.episodes, num=num)
    sources = CONTEXT.get_sources(ep)
    return render_template('anime_source_block.j2',
                           sources=sources,
                           fn_urlspit=urlsplit  # enchant render source element
                           )


@app.get('/get_videos')
def anime_videos():
    title = request.args.get('title').strip()
    url = request.args.get('url').strip()
    source = match_item_by_kwargs(CONTEXT.sources, title=title, url=url)
    CONTEXT.picked_source = source

    videos = CONTEXT.get_videos(source)
    if app.config['cli_args']['quality'] == 0:
        return render_template('anime_videos_block.j2',
                               videos=videos,
                               fn_urlspit=urlsplit)  # enchant render source element

    video = get_video_by_quality(
        app.config['cli_args']['quality'],
        CONTEXT.get_videos(source)
    )
    return render_template('anime_player_js_block.j2', video=video)


@app.get('/spawn_player')
def anime_spawn_player():
    """spawn js player in web"""
    # '{"quality": "{{ video.quality }}", "type": "{{ video.type }}", "url": "{{ video.url }}"}'
    url = request.args.get('url').strip()
    quality = int(request.args.get('quality').strip())
    type_ = request.args.get('type').strip()

    video = match_item_by_kwargs(CONTEXT.videos, quality=quality, type=type_, url=url)
    CONTEXT.picked_video = video

    return render_template('anime_player_js_block.j2', video=video)
