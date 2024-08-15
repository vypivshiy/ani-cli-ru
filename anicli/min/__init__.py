"""minimal realisation CLI app with minimal dependencies.

just like in the very first implementations of this project
"""
from typing import TYPE_CHECKING, List, TypeVar, Tuple, Union, Dict, Optional

from anicli_api.tools.m3u import Playlist

from ..libs.mpv_json_ipc import MPV
from ..types_ import TYPER_CONTEXT_OPTIONS
from ..utils import get_video_by_quality
from ..utils.anicli_api_helpers import iter_slice_videos, new_tmp_playlist
from ..utils.fetch_extractors import import_extractor
from ..utils.str_formatters import progress_bar

if TYPE_CHECKING:
    from anicli_api.base import BaseOngoing, BaseSearch, BaseAnime, BaseSource, Video, BaseEpisode

T = TypeVar("T")

_INTRO = """anicli-ru min
Type 'h' for get available commands
"""
_HELP = {
    "h": "show help message or print picked items",
    "o": "get ongoings",
    "s <query>": "search title by query",
    "q": "exit from app",
    "b": 'back to prev step',
    'stop': 'MPV PLAYER: stop playing video',
}

# in init state load
GLOBAL_OPTIONS: TYPER_CONTEXT_OPTIONS = {}  # type: ignore
MPV_SOCKET = MPV()


# helpers functions
def _print_sequence(items: List[T], limit: int = 20) -> None:
    if len(items) <= limit + 4:
        print(*[f'[{i}] {item}' for i, item in enumerate(items, 1)], sep='\n')
        return

    slice_1 = items[:limit]
    slice_2 = items[-3:]
    last_items_counter = len(items) - 3

    print(*[f'[{i}] {item}' for i, item in enumerate(slice_1, 1)], sep='\n')
    print('...')
    print(*[f'[{i}] {item}' for i, item in enumerate(slice_2, last_items_counter)], sep='\n')


def _check_pick_by_index(items: List[T], prompt: str) -> bool:
    """return true if index is valid for items sequence"""
    return prompt.isdigit() and 0 < int(prompt) <= len(items)


def _check_pick_by_slice(items: List[T], prompt: str) -> bool:
    """return true if prompt is a valid slice for items sequence"""
    if len(prompt.split('-')) != 2:
        return False

    print(prompt, 'TEST')
    start, end = prompt.split('-')
    if not start.isdigit() and not end.isdigit():
        return False

    start_int, end_int = int(start), int(end)
    if start_int >= end_int:
        return False
    elif start_int <= len(items) and end_int <= len(items):
        return True

    return False


def _suggest_exit() -> None:
    prompt = input("exit ([y]/n")
    if not prompt or prompt.lower() == 'y':
        try:
            MPV_SOCKET.terminate()
        finally:
            exit(1)


def loop_input(prompt: str = "> "):
    while True:
        try:
            inpt = input(prompt)
            if inpt == 'q':
                _suggest_exit()
            elif inpt == 'stop':
                try:
                    MPV_SOCKET.command('stop')
                    print('stop playing video')
                except BrokenPipeError:
                    pass
            else:
                yield inpt
        except (KeyboardInterrupt, EOFError):
            _suggest_exit()


# END


def main(options: TYPER_CONTEXT_OPTIONS):
    global GLOBAL_OPTIONS
    # options
    GLOBAL_OPTIONS.update(options)
    extractor = import_extractor(options['source'])()

    print(_INTRO)
    for prompt in loop_input():
        if prompt == 'h':
            print('\n'.join(f'{k} - {v}' for k, v in _HELP.items()))

        elif prompt == 'o':
            handle_ongoing(extractor.ongoing())

        elif prompt.startswith('s') and len(prompt.split()) >= 2:
            _, query = prompt.split(maxsplit=1)
            result = extractor.search(query)
            if not result:
                print('not found')
                continue
            handle_search(result)


def handle_ongoing(ongs: List['BaseOngoing']):
    _print_sequence(ongs)
    for prompt in loop_input('ongoing> '):
        if prompt == 'b':
            return
        elif _check_pick_by_index(ongs, prompt):
            ong = ongs[int(prompt) - 1]
            return handle_anime(ong.get_anime())


def handle_search(seraches: List['BaseSearch']):
    _print_sequence(seraches)
    print(f'pick num [1-{len(seraches)}]')
    for prompt in loop_input('search> '):
        if prompt == 'b':
            return
        elif prompt == 'h':
            _print_sequence(seraches)

        elif _check_pick_by_index(seraches, prompt):
            item = seraches[int(prompt) - 1]
            handle_anime(item.get_anime())


def handle_anime(anime: 'BaseAnime'):
    episodes: List['BaseEpisode'] = anime.get_episodes()
    if not episodes:
        print('not found')
        return
    _print_sequence(episodes)
    print(f'pick num [1-{len(episodes)}] or slice')
    for prompt in loop_input('anime> '):
        if prompt == 'b':
            return

        elif prompt == 'h':
            _print_sequence(episodes)

        elif _check_pick_by_slice(episodes, prompt):
            start, end = (int(i) for i in prompt.split('-'))
            sources = episodes[start].get_sources()
            if not sources:
                print('not found')
                continue

            handle_slice_sources(anime, episodes[start - 1: end], sources)

        elif _check_pick_by_index(episodes, prompt):
            item = episodes[int(prompt) - 1]
            sources = item.get_sources()
            if not sources:
                print('not found')
                continue
            handle_sources(sources)


def handle_slice_sources(anime: 'BaseAnime', episodes: List['BaseEpisode'], sources: List['BaseSource']):
    _print_sequence(sources)
    print(f'pick num [1-{len(sources)}]')

    for prompt in loop_input('slice-source> '):
        if prompt == 'b':
            return
        elif prompt == 'h':
            _print_sequence(sources)

        elif _check_pick_by_index(sources, prompt):
            source = sources[int(prompt) - 1]
            videos = source.get_videos()
            if not videos:
                print('not found')
                continue
            handle_slice_videos(anime,
                                episodes,
                                source,
                                videos)


def handle_slice_videos(anime: 'BaseAnime', episodes: List['BaseEpisode'], source: 'BaseSource', videos: List['Video']):
    if GLOBAL_OPTIONS['quality'] != 0:
        video = get_video_by_quality(GLOBAL_OPTIONS['quality'], videos)
    else:
        _print_sequence(videos)
        print(f'pick num [1-{len(videos)}]')
        for prompt in loop_input('slice-video> '):
            if prompt == 'b':
                return
            elif prompt == 'h':
                _print_sequence(videos)

            elif _check_pick_by_index(videos, prompt):
                video = videos[int(prompt) - 1]
                break

    cache: List[Tuple[Video, str]] = []
    for i, (video, title) in progress_bar(enumerate(iter_slice_videos(anime=anime,
                                                                      episodes=episodes,
                                                                      # get object from infinite loop
                                                                      start_video=video,  # type: ignore
                                                                      start_source=source), 1)):
        if i == GLOBAL_OPTIONS['m3u_size']:
            raw_playlist = Playlist.from_videos(
                videos=[i[0] for i in cache],
                names=[i[1] for i in cache]
            )
            play_playlist(raw_playlist, video.headers)
            cache.clear()
        cache.append((video, title))

    # finally play last cached video
    if cache:
        raw_playlist = Playlist.from_videos(
            videos=[i[0] for i in cache],
            names=[i[1] for i in cache]
        )
        play_playlist(raw_playlist, video.headers)
        cache.clear()
    return


def handle_sources(sources: List['BaseSource']):
    _print_sequence(sources)
    print(f'pick num [1-{len(sources)}]')

    for prompt in loop_input('source> '):
        if prompt == 'b':
            return

        elif prompt == 'h':
            _print_sequence(sources)

        elif _check_pick_by_index(sources, prompt):
            item = sources[int(prompt) - 1]
            videos = item.get_videos()
            if not videos:
                print('not found')
                continue
            handle_video(videos)


def handle_video(videos: List['Video']):
    if GLOBAL_OPTIONS['quality'] != 0:
        video = get_video_by_quality(GLOBAL_OPTIONS['quality'], videos)
        play_video(video)
        return

    else:
        _print_sequence(videos)
        print(f'pick num [1-{len(videos)}]')
        for prompt in loop_input('video> '):
            if prompt == 'b':
                return
            elif prompt == 'h':
                _print_sequence(videos)

            elif _check_pick_by_index(videos, prompt):
                video = videos[int(prompt) - 1]
                play_video(video)
                return


def play_video(video: Union['Video', str]) -> None:
    global MPV_SOCKET

    if video.headers:
        # reload MPV socket process with headers args
        MPV_SOCKET.terminate()
        MPV_SOCKET = MPV(http_headers=video.headers)
    try:
        print('play single video')
        MPV_SOCKET.play(video.url)
    # socket closed, reopen
    except BrokenPipeError:
        MPV_SOCKET = MPV(http_headers=video.headers)
        play_video(video)


def play_playlist(playlist: str, headers: Optional[Dict[str, str]]) -> None:
    global MPV_SOCKET

    if headers:
        # reload MPV socket process with headers args
        MPV_SOCKET.terminate()
        MPV_SOCKET = MPV(http_headers=headers)
    try:
        print('play playlist video')
        with new_tmp_playlist(playlist) as f_name:
            MPV_SOCKET.play(f_name)
    # socket closed, reopen
    except BrokenPipeError:
        MPV_SOCKET = MPV(http_headers=headers)
        play_playlist(playlist, headers)
