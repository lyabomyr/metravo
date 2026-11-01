"""FastAPI dependencies that every protected router uses."""

from __future__ import annotations

from fastapi import Depends, Header, Request

from ...core.container import Container
from ...core.errors import Forbidden, Unauthorized
from ..users.models import User


def get_container(request: Request) -> Container:
    return request.app.state.container


def current_user(
    authorization: str = Header(default=""),
    container: Container = Depends(get_container),
) -> User:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise Unauthorized("Sign in first")
    return container.auth.user_from_token(token)


def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise Forbidden("Admins only")
    return user
