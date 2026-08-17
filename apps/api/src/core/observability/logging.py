from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from core.config.settings import get_settings
from core.multitenancy.context import TenantNotSetError, get_current_tenant_id
from core.observability.context import get_correlation_id, get_request_id

_STANDARD_LOG_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__)

_REDACTED_KEYS = frozenset(
    {"password", "senha", "senha_hash", "token", "secret", "authorization", "jwt", "credential"}
)


class JsonFormatter(logging.Formatter):
    """Renders one log line as a single JSON object — every field explicit
    (never a free-text message a downstream tool has to parse), matching
    ``docs/backend/OBSERVABILITY.md``: ``request_id``/``correlation_id``/
    ``tenant_id``/``user_id`` are attached automatically from context when
    available, never passed by hand at each call site.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()
        if request_id is not None:
            payload["request_id"] = request_id

        correlation_id = get_correlation_id()
        if correlation_id is not None:
            payload["correlation_id"] = correlation_id

        try:
            payload["tenant_id"] = str(get_current_tenant_id())
        except TenantNotSetError:
            pass

        for key, value in record.__dict__.items():
            if key in _STANDARD_LOG_RECORD_ATTRS or key in payload:
                continue
            payload[key] = "***REDACTED***" if key.lower() in _REDACTED_KEYS else value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configures structured, single-format JSON logging for the whole
    process. Called once from ``main.py`` at application startup, before
    anything else runs, so every module can simply use
    ``logging.getLogger(__name__)``.
    """

    settings = get_settings()
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level)

    # SQLAlchemy's own engine logger is chatty at INFO — keep it at WARNING
    # unless the app itself is in DEBUG, matching ``settings.debug``'s
    # existing ``echo=`` behavior on the engine (core/database/session.py).
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
