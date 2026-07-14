"""
CyberRisk360

Purpose:
Application logging setup. A single configured logger namespace
("cyberrisk360") with either human-readable console output or one JSON
object per line (LOG_FORMAT=json) for log aggregators.

Kept on its own namespace (not the root logger) so it doesn't clobber
uvicorn's access/error logging.
"""

import json
import logging
import sys

from app.core.config import LOG_LEVEL, LOG_FORMAT


LOGGER_NAME = "cyberrisk360"

# Structured fields the request middleware attaches via `extra=`.
_EXTRA_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client_ip",
)


class JsonFormatter(logging.Formatter):
    """
    Render a log record as a single-line JSON object.
    """

    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def configure_logging():
    """
    Configure the application logger. Idempotent - safe to call more
    than once (e.g. across multiple import entrypoints).
    """

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    # Replace handlers so repeated calls don't stack duplicates.
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if LOG_FORMAT == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
        )

    logger.addHandler(handler)

    return logger


def get_logger(name: str = None):
    """
    Return the app logger, or a child of it (`cyberrisk360.<name>`).
    """

    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")

    return logging.getLogger(LOGGER_NAME)
