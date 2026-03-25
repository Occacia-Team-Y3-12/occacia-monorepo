from __future__ import annotations

import inspect
import sys

import structlog
from fastapi_structlog import LogSettings, setup_logger

from app.core.config import Settings


def configure_logging(settings: Settings) -> structlog.BoundLogger:
    """
    Configure structlog via fastapi-structlog. Falls back to defaults if the
    installed version exposes a different setup signature.
    """
    json_logs = settings.LOG_JSON
    if json_logs is None:
        json_logs = not sys.stdout.isatty()
        if settings.LOG_PRETTY and sys.stdout.isatty():
            json_logs = False

    log_level = settings.LOG_LEVEL
    debug = log_level.upper() == "DEBUG"

    # Prefer LogSettings, but tolerate differing signatures.
    try:
        log_settings = LogSettings(
            log_level=log_level,
            json_logs=json_logs,
            debug=debug,
        )
        setup_logger(log_settings)
    except Exception:
        try:
            sig = inspect.signature(setup_logger)
            kwargs = {}
            if "settings_" in sig.parameters:
                kwargs["settings_"] = log_settings
                setup_logger(**kwargs)
                return structlog.get_logger("occacia")
            if "log_level" in sig.parameters:
                kwargs["log_level"] = log_level
            if "json_logs" in sig.parameters:
                kwargs["json_logs"] = json_logs
            setup_logger(**kwargs)
        except Exception:
            setup_logger(LogSettings())

    return structlog.get_logger("occacia")
