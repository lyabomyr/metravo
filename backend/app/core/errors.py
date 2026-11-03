"""Typed domain errors. Services raise these; ``core/http.py`` maps them to HTTP.

An error carries a message key from ``core/i18n`` and its parameters, so the
same error reads in the language of whoever receives it. ``message`` is the
English text, for logs and tests.
"""

from .i18n import translator


class Term(str):
    """A parameter that is itself a message key ("deal.rent"), so it is translated along with the message."""


class AppError(Exception):
    status_code = 400

    def __init__(self, key: str, /, **params):  # positional-only: a param may be called "key"
        self.key = key
        self.params = params
        self.message = self.text("en")
        super().__init__(self.message)

    def text(self, locale: str) -> str:
        params = {name: translator.t(locale, value) if isinstance(value, Term) else value for name, value in self.params.items()}
        return translator.t(locale, self.key, **params)


class Invalid(AppError):
    status_code = 422


class Unauthorized(AppError):
    status_code = 401


class LimitReached(AppError):
    """The user's plan does not allow this. The frontend offers an upgrade."""

    status_code = 402


class Forbidden(AppError):
    status_code = 403


class NotFound(AppError):
    status_code = 404


class Unavailable(AppError):
    """Something we depend on failed; trying again later may work."""

    status_code = 503
