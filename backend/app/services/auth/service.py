from __future__ import annotations

from dataclasses import dataclass

from ...core.errors import Invalid
from ...core.service import BaseService
from ..users.models import User
from ..users.service import UserService
from .providers.base import IdentityProvider
from .tokens import SessionTokenService


@dataclass(frozen=True)
class Session:
    token: str
    user: User
    is_new: bool


class AuthService(BaseService):
    def __init__(
        self,
        providers: list[IdentityProvider],
        users: UserService,
        tokens: SessionTokenService,
    ):
        super().__init__()
        self._providers = {provider.name: provider for provider in providers}
        self._users = users
        self._tokens = tokens

    @property
    def provider_names(self) -> list[str]:
        return list(self._providers)

    def sign_in(self, provider_name: str, credential: str) -> Session:
        provider = self.require(
            self._providers.get(provider_name),
            Invalid(f"Sign-in method '{provider_name}' is not enabled"),
        )
        identity = provider.verify(credential)
        user, is_new = self._users.sign_in(identity.email)
        return Session(token=self._tokens.issue(user.id), user=user, is_new=is_new)

    def user_from_token(self, token: str) -> User:
        return self._users.get(self._tokens.user_id_from(token))
