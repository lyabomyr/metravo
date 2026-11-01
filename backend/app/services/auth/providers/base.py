from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Identity:
    """A person whose email address a provider has vouched for."""

    email: str
    provider: str


class IdentityProvider(ABC):
    """Turns a credential from the frontend into a verified email address."""

    name: str

    @abstractmethod
    def verify(self, credential: str) -> Identity:
        """Return the identity or raise ``Unauthorized``."""
