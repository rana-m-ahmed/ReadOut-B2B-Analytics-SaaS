"""Application error handling."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


@dataclass(slots=True)
class AppError(Exception):
    """Base class for application-safe API errors."""

    message: str
    code: str
    status_code: int


class ValidationError(AppError):
    """Raised when request or domain validation fails."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message=message, code="validation_error", status_code=400)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, code="not_found", status_code=404)


class RateLimitedError(AppError):
    """Raised when a request is rate limited."""

    def __init__(self, message: str = "Request rate limited") -> None:
        super().__init__(message=message, code="rate_limited", status_code=429)


class UpstreamLLMError(AppError):
    """Raised when the upstream LLM provider fails."""

    def __init__(self, message: str = "Upstream LLM request failed") -> None:
        super().__init__(message=message, code="upstream_llm_error", status_code=502)


class QueryCompilationError(AppError):
    """Raised when NLQ cannot compile into a safe analytic query."""

    def __init__(self, message: str = "Query compilation failed") -> None:
        super().__init__(message=message, code="query_compilation_error", status_code=400)


class UnauthorizedError(AppError):
    """Raised when request authentication fails."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message=message, code="unauthorized", status_code=401)


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Render typed application errors into a stable JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for application-safe errors."""
    app.add_exception_handler(AppError, app_error_handler)
