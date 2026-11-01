from __future__ import annotations

from pydantic import BaseModel

from ..users.models import User


class SignInRequest(BaseModel):
    provider: str
    credential: str


class UserOut(BaseModel):
    id: str
    email: str
    plan: str
    is_admin: bool
    created_at: str

    @classmethod
    def of(cls, user: User) -> UserOut:
        return cls(id=user.id, email=user.email, plan=user.plan, is_admin=user.is_admin, created_at=user.created_at)


class SessionOut(BaseModel):
    token: str
    user: UserOut
    is_new: bool
