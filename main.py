import logging

from anicli_api.loader import ExtractorLoader
import click


from anicli.config import dp
from anicli.commands.tools import SingletonStorage

loger = logging.getLogger()
loger.setLevel(logging.ERROR)

@click.command()
@click.option("-s", "--source", "source",
              default="animego",
              type=click.Choice(["animego", "anilibria", "animevost", "animania", "animejoy"]),
              help="Anime source.",
              show_default=True)
def load_options(source):
    print(f"anicli_api.extractors.{source}")
    anime_extractor = ExtractorLoader.load(f"anicli_api.extractors.{source}")
    SingletonStorage().extractor_module = anime_extractor
    dp.run()


if __name__ == '__main__':
    load_options()
