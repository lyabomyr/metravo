from __future__ import annotations

from .base import Identity, IdentityProvider


class DevIdentityProvider(IdentityProvider):
    """Trusts whatever email it is given.

    Exists so the whole product runs locally and in e2e tests without a
    Firebase project. ``Settings.validate`` refuses to start production with it.
    """

    name = "dev"

    def verify(self, credential: str) -> Identity:
        return Identity(email=credential, provider=self.name)
