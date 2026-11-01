from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.container import Container
from ..users.models import User
from .dependencies import current_user, get_container
from .schemas import SessionOut, SignInRequest, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/session", response_model=SessionOut)
def sign_in(body: SignInRequest, container: Container = Depends(get_container)) -> SessionOut:
    session = container.auth.sign_in(body.provider, body.credential)
    return SessionOut(token=session.token, user=UserOut.of(session.user), is_new=session.is_new)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.of(user)
