"""Supabase JWT authentication and anonymous workspace provisioning."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

import jwt
from fastapi import Depends, Request
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel, ConfigDict

from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.db.models import WorkspaceCreate
from app.db.repositories import DatasetRepository, WorkspaceRepository


class CurrentUser(BaseModel):
    """Authenticated Supabase user context."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    is_anonymous: bool
    workspace_id: UUID | None = None
    demo_dataset_id: UUID | None = None


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise UnauthorizedError("Invalid Authorization header")
    return token.strip()


def _decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except ExpiredSignatureError as exc:
        raise UnauthorizedError("Token expired") from exc
    except InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token") from exc


def _build_current_user(claims: dict[str, Any]) -> CurrentUser:
    subject = claims.get("sub")
    if not subject:
        raise UnauthorizedError("Token missing subject")

    app_metadata = claims.get("app_metadata") or {}
    is_anonymous = bool(app_metadata.get("is_anonymous", False))
    try:
        user_id = UUID(str(subject))
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Token subject must be a valid UUID") from exc
    return CurrentUser(user_id=user_id, is_anonymous=is_anonymous)


def ensure_workspace(
    current_user: CurrentUser,
    workspace_repository: WorkspaceRepository,
    dataset_repository: DatasetRepository,
    ttl_hours: int,
    *,
    now_factory: Callable[[], datetime] | None = None,
) -> CurrentUser:
    """Ensure anonymous users have a single TTL workspace and demo dataset reference."""

    if not current_user.is_anonymous:
        return current_user

    now_factory = now_factory or (lambda: datetime.now(timezone.utc))
    workspaces = workspace_repository.list_for_owner(current_user.user_id)
    workspace = workspaces[0] if workspaces else None

    if workspace is None:
        created_workspace = workspace_repository.create(
            current_user.user_id,
            WorkspaceCreate(
                name="Anonymous Workspace",
                slug=f"anon-{current_user.user_id.hex[:12]}",
                is_anonymous=True,
                expires_at=now_factory() + timedelta(hours=ttl_hours),
            ),
        )
        current_user.workspace_id = created_workspace.id
    else:
        current_user.workspace_id = workspace.id

    demo_dataset = dataset_repository.get_demo_dataset()
    current_user.demo_dataset_id = demo_dataset.id if demo_dataset is not None else None
    return current_user


async def resolve_current_user(
    request: Request,
    settings: Settings,
    workspace_repository: WorkspaceRepository,
    dataset_repository: DatasetRepository,
) -> CurrentUser:
    """Decode a Supabase JWT and provision anonymous state when needed."""

    token = _extract_bearer_token(request)
    claims = _decode_supabase_jwt(token, settings)
    current_user = _build_current_user(claims)
    return ensure_workspace(
        current_user,
        workspace_repository,
        dataset_repository,
        settings.ANON_SESSION_TTL_HOURS,
    )


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """FastAPI dependency returning the authenticated current user."""

    workspace_repository = WorkspaceRepository()
    dataset_repository = DatasetRepository()
    return await resolve_current_user(
        request,
        settings,
        workspace_repository,
        dataset_repository,
    )
