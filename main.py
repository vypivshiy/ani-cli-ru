from anicli_api.loader import ExtractorLoader
import click


from anicli.config import dp
from anicli.commands.options import EXTRACTOR
from anicli.commands.tools import SingletonStorage


@click.command()
@click.option("-s", "--source", "source",
              default="animego",
              type=click.Choice(["animego", "anilibria", "animevost", "animania"]),
              help="Anime source.",
              show_default=True)
def load_options(source):
    anime_extractor = ExtractorLoader.load(f"anicli_api.extractors.{source}")
    SingletonStorage().extractor = anime_extractor.Extractor()
    dp.run()


if __name__ == '__main__':
    load_options()
