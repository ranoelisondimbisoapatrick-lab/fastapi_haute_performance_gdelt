"""app.core.logging

JSON logging configuration (production-friendly).

Goals:
- Structured logs (JSON) to integrate with ELK/Datadog/Grafana Loki.
- Log to stdout to work well in Docker/Kubernetes.
- Avoid duplicate handlers on reload.

In this repo:
- `configure_logging()` is called at startup from app.main or worker entrypoints.
"""

from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger

from .config import settings


def configure_logging() -> None:
    """Configure root logger with a JSON formatter."""
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d"
    )
    handler.setFormatter(formatter)

    # Reset handlers to avoid duplicates during reload.
    logger.handlers = [handler]
