"""Per-user API rate limiting for expensive endpoints.

This module owns backend-side throttling for ReadOut's expensive routes. It is
deliberately separate from `nlq.groq_client`, whose reactive backoff responds to
provider 429s after a request has already left our backend. The limiter here
protects our own capacity before we spend Groq quota or tie up app workers.

The current MVP implementation uses an in-memory sliding-window store. Route
dependencies depend on the small `RateLimitStore` interface so a Redis-backed
implementation can replace it later without changing the route modules.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import ceil
from threading import Lock
from time import monotonic
from typing import Annotated, Protocol
from uuid import UUID

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.errors import RateLimitedError
from app.security.auth_guard import CurrentUser, get_current_user


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Outcome of a single rate-limit check."""

    allowed: bool
    remaining: int
    retry_after_seconds: int


class RateLimitStore(Protocol):
    """Storage contract for per-key sliding-window rate limiting."""

    def check(self, key: str, *, limit: int, window_seconds: int, now: float | None = None) -> RateLimitDecision:
        """Evaluate and record one request attempt for the given key."""


class InMemorySlidingWindowRateLimitStore:
    """Thread-safe in-memory sliding-window limiter state."""

    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str, *, limit: int, window_seconds: int, now: float | None = None) -> RateLimitDecision:
        current = monotonic() if now is None else now
        window_start = current - window_seconds

        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            while bucket and bucket[0] <= window_start:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = max(1, ceil(window_seconds - (current - bucket[0])))
                return RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    retry_after_seconds=retry_after,
                )

            bucket.append(current)
            return RateLimitDecision(
                allowed=True,
                remaining=max(0, limit - len(bucket)),
                retry_after_seconds=0,
            )


_rate_limit_store: RateLimitStore = InMemorySlidingWindowRateLimitStore()


def get_rate_limit_store() -> RateLimitStore:
    """Return the shared rate-limit store instance."""

    return _rate_limit_store


def reset_rate_limit_store() -> None:
    """Reset the shared store for tests or local dev reloads."""

    global _rate_limit_store
    _rate_limit_store = InMemorySlidingWindowRateLimitStore()


def enforce_rate_limit_for_user(
    user_id: UUID,
    *,
    scope: str,
    limit: int,
    window_seconds: int,
    store: RateLimitStore,
    now: float | None = None,
) -> None:
    """Apply a per-user sliding-window limit and raise a typed 429 on overflow."""

    decision = store.check(
        f"{scope}:{user_id}",
        limit=limit,
        window_seconds=window_seconds,
        now=now,
    )
    if decision.allowed:
        return

    raise RateLimitedError(
        f"Too many requests for {scope}. Try again in {decision.retry_after_seconds} seconds."
    )


def build_user_rate_limit_dependency(
    *,
    scope: str,
    limit_setting: str,
    window_setting: str,
):
    """Create a FastAPI dependency that rate-limits the authenticated user."""

    async def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
        settings: Annotated[Settings, Depends(get_settings)],
        store: Annotated[RateLimitStore, Depends(get_rate_limit_store)],
    ) -> None:
        enforce_rate_limit_for_user(
            current_user.user_id,
            scope=scope,
            limit=int(getattr(settings, limit_setting)),
            window_seconds=int(getattr(settings, window_setting)),
            store=store,
        )

    dependency.__name__ = f"enforce_{scope.replace('-', '_')}_rate_limit"
    return dependency


enforce_ask_rate_limit = build_user_rate_limit_dependency(
    scope="ask",
    limit_setting="ASK_RATE_LIMIT_REQUESTS",
    window_setting="ASK_RATE_LIMIT_WINDOW_SECONDS",
)

enforce_upload_url_rate_limit = build_user_rate_limit_dependency(
    scope="datasets_upload_url",
    limit_setting="UPLOAD_URL_RATE_LIMIT_REQUESTS",
    window_setting="UPLOAD_URL_RATE_LIMIT_WINDOW_SECONDS",
)
