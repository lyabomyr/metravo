from __future__ import annotations

from datetime import timedelta

import jwt

from ...core.clock import Clock
from ...core.errors import Unauthorized

ALGORITHM = "HS256"


class SessionTokenService:
    """Issues and checks our own session tokens.

    Identity providers are only consulted once, at sign-in. After that every
    request carries this token, so the API does not depend on which provider
    the user signed in with.
    """

    def __init__(self, secret: str, ttl_hours: int, clock: Clock):
        self._secret = secret
        self._ttl = timedelta(hours=ttl_hours)
        self._clock = clock

    def issue(self, user_id: str) -> str:
        now = self._clock.now()
        claims = {"sub": user_id, "iat": now, "exp": now + self._ttl}
        return jwt.encode(claims, self._secret, algorithm=ALGORITHM)

    def user_id_from(self, token: str) -> str:
        try:
            claims = jwt.decode(token, self._secret, algorithms=[ALGORITHM])
        except jwt.PyJWTError as exc:
            raise Unauthorized("auth.session_expired") from exc
        return claims["sub"]
