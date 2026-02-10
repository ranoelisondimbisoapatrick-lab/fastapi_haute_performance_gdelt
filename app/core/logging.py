import logging
import sys
from pythonjsonlogger import jsonlogger
from .config import settings


def configure_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d"
    )
    handler.setFormatter(fmt)

    # Reset handlers (avoid duplicates in reload)
    logger.handlers = [handler]
