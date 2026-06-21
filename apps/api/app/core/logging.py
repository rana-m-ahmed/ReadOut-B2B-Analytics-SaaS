"""Application logging."""

from __future__ import annotations

import json
import logging
import sys
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class JsonFormatter(logging.Formatter):
    """Serialize structured log records as compact JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("method", "path", "status", "duration_ms", "request_id"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging() -> None:
    """Configure the application logger for JSON output."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("readout.api")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach request IDs and emit one structured log record per request."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.logger = logging.getLogger("readout.api")

    async def dispatch(self, request: Request, call_next):
        request_id = uuid4().hex
        request.state.request_id = request_id
        started_at = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        self.logger.info(
            "request_complete",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )
        return response
