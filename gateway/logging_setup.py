import logging
import logging.config
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from gateway.settings import Settings


def _default_formatter() -> logging.Formatter:
    return jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
        timestamp=True,
        json_ensure_ascii=False,
    )


def configure_logging(settings: Settings) -> None:
    """Configure JSON structured logging for the service."""

    formatter = _default_formatter()
    handler: Dict[str, Any] = {
        "class": "logging.StreamHandler",
        "level": settings.log_level.upper(),
        "formatter": "json",
        "stream": "ext://sys.stdout",
    }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": jsonlogger.JsonFormatter,
                    "fmt": formatter._fmt,
                    "rename_fields": {"asctime": "timestamp", "levelname": "level"},
                }
            },
            "handlers": {"default": handler},
            "root": {"handlers": ["default"], "level": settings.log_level.upper()},
        }
    )

    logging.getLogger(__name__).info("Logging configured", extra={"level": settings.log_level})
