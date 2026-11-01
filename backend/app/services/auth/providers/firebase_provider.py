from __future__ import annotations

import jwt

from ....core.errors import Unauthorized
from .base import Identity, IdentityProvider

# Google publishes the keys Firebase signs ID tokens with. Verifying against
# them locally means no Admin SDK and no service-account secret on our side.
GOOGLE_JWKS_URL = "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"


class FirebaseIdentityProvider(IdentityProvider):
    """Verifies a Firebase Auth ID token (email link or Google sign-in)."""

    name = "firebase"

    def __init__(self, project_id: str, jwks_client: jwt.PyJWKClient | None = None):
        self._project_id = project_id
        self._jwks = jwks_client or jwt.PyJWKClient(GOOGLE_JWKS_URL)

    def verify(self, credential: str) -> Identity:
        try:
            key = self._jwks.get_signing_key_from_jwt(credential).key
            claims = jwt.decode(
                credential,
                key,
                algorithms=["RS256"],
                audience=self._project_id,
                issuer=f"https://securetoken.google.com/{self._project_id}",
            )
        except jwt.PyJWTError as exc:
            raise Unauthorized(f"Invalid Firebase token: {exc}") from exc
        if not claims.get("email") or not claims.get("email_verified"):
            raise Unauthorized("Firebase account has no verified email")
        return Identity(email=claims["email"], provider=self.name)
