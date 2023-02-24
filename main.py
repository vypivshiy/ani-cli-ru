import logging

from anicli_api.loader import ExtractorLoader
import click


from anicli.config import dp
from anicli.commands.tools import SingletonStorage
from anicli.commands import options


loger = logging.getLogger()
loger.setLevel(logging.ERROR)

@click.command()
@click.option("-s", "--source", "source",
              default="animego",
              type=click.Choice(["animego", "anilibria", "animevost", "animania", "animejoy"]),
              help="Anime source.",
              show_default=True)
@click.option("-P", "--video-player", "video_player",
              default="mpv",
              help="Video player. EXAMPLE: anicli -P 'mpv --vo=gpu --hwdec=vaapi-copy'",
              show_default=True)
def load_options(source, video_player):
    print(f"anicli_api.extractors.{source}")
    anime_extractor = ExtractorLoader.load(f"anicli_api.extractors.{source}")
    SingletonStorage().extractor_module = anime_extractor
    options.PLAYER, *options.EXTRA_ATTRS = video_player.split()
    dp.run()


if __name__ == '__main__':
    load_options()
