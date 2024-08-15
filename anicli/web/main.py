from urllib.parse import urlsplit
from anicli_api.source.animego import Extractor
from flask import Flask, render_template, request

from ..utils.cached_extractor import CachedExtractor, CachedItemContext
from ..utils.fetch_extractors import get_extractor_modules

app = Flask(__name__)

EX = CachedExtractor(Extractor())
CONTEXT = CachedItemContext(extractor=EX)


# {ongoing: {}, search: {}, anime: {}, episodes: {}, sources: {}, video: {} }

@app.get('/')
def main():
    modules = get_extractor_modules()

    ongoings_results = CONTEXT.ongoing()
    ongoings_element = render_template('ongoings_block.j2', ongoings_results=ongoings_results)
    select_providers = render_template('extractor_providers_block.j2', modules=modules)

    return render_template('index.j2',
                           select_providers=select_providers,
                           ongoings=ongoings_element
                           )


@app.get('/search')
def search():
    # TODO: validate
    query = request.args.get('query', '')

    searches = CONTEXT.search(query)
    return render_template('search.j2', search_results=searches, title=f"Search {query}")


@app.post('/anime')
def anime_page():
    title = request.form['title']
    url = request.form['url']

    # HACK: get search/ongoing from cache by title and url
    match_item = [o for o in CONTEXT.searches_or_ongoings if o.title == title and o.url == url][0]
    anime = CONTEXT.get_anime(match_item)
    episodes = CONTEXT.get_episodes()
    return render_template('anime.j2', title=anime.title, episodes=episodes, anime=anime)


@app.get('/get_sources')
def anime_sources():
    num = request.args.get('num').strip()
    ep = [e for e in CONTEXT.episodes if e.num == num][0]
    sources = CONTEXT.get_sources(ep)
    return render_template('anime_source_block.j2',
                           sources=sources,
                           fn_urlspit=urlsplit  # enchant render source element
                           )


@app.get('/get_videos')
def anime_videos():
    title = request.args.get('title').strip()
    url = request.args.get('url').strip()

    source = [s for s in CONTEXT.sources if s.title == title and s.url == url][0]
    CONTEXT.picked_source = source

    videos = CONTEXT.get_videos(source)
    return render_template('anime_videos_block.j2',
                           videos=videos,
                           fn_urlspit=urlsplit)  # enchant render source element


@app.get('/spawn_player')
def anime_spawn_player():
    # '{"quality": "{{ video.quality }}", "type": "{{ video.type }}", "url": "{{ video.url }}"}'
    url = request.args.get('url').strip()
    quality = int(request.args.get('quality').strip())
    type_ = request.args.get('type').strip()

    video = [v for v in CONTEXT.videos if v.url == url and v.quality == quality and v.type == type_][0]
    CONTEXT.picked_video = video

    return render_template('anime_player_js_block.j2', video=video)


if __name__ == '__main__':
    app.run(debug=True)
