from typing import TYPE_CHECKING, List

from tqdm import tqdm

from anicli.cli.player import run_video, run_m3u_playlist
from anicli.cli.video_utils import slice_playlist_iter
from anicli.utils import create_title

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseEpisode
    from anicli.cli import AnicliApp


def play_slice_urls(*, anime: "BaseAnime", episodes: List["BaseEpisode"], cmp_key_hash: int, app: "AnicliApp"):
    for episode, source, video in slice_playlist_iter(episodes, cmp_key_hash, app.CFG):
        title = create_title(anime, episode, source)
        run_video(video, title, player=app.CFG.PLAYER, use_ffmpeg=app.CFG.USE_FFMPEG_ROUTE)


def play_slice_playlist(*, anime: "BaseAnime", episodes: List["BaseEpisode"], cmp_key_hash: int, app: "AnicliApp"):
    # TODO increase speed
    videos, names = [], []
    playlist_iter = enumerate(slice_playlist_iter(episodes, cmp_key_hash, app.CFG))
    progress = tqdm(playlist_iter, desc="create m3u playlist")

    for i, ctx in progress:
        episode, source, video = ctx
        if i % app.CFG.M3U_MAX_SIZE == 0 and i != 0:
            run_m3u_playlist(videos=videos, names=names, quality=app.CFG.MIN_QUALITY)
            videos.clear()
            names.clear()
        videos.append(video)
        names.append(create_title(anime, episode, source))

    if videos and names:
        run_m3u_playlist(videos=videos, names=names, quality=app.CFG.MIN_QUALITY)
