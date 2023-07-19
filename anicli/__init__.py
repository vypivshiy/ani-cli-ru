from anicli.cli import APP
import importlib
__version__ = "5.0.0"


def run_cli():
    import argparse
    parser = argparse.ArgumentParser(description="anicli-ru")
    parser.add_argument("-s", "--source", default="animego", choices=["animego", "sovetromantica",
                                                                      "animejoy",
                                                                      "anilibria",
                                                                      "animevost"],
                        help="Anime source provider. DEFAULT `animego`")
    namespaces = parser.parse_args()
    module = importlib.import_module(f"anicli_api.source.{namespaces.source}")
    APP.CTX["EXTRACTOR"] = getattr(module, "Extractor")()
    APP.loop()


if __name__ == '__main__':
    run_cli()
