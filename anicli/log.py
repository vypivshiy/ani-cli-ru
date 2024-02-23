import logging

__all__ = ["logger"]


handler = logging.StreamHandler()
_formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s")

logger = logging.getLogger("anicli-ru")  # type: ignore
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
