"""Typed domain errors. Services raise these; ``core/http.py`` maps them to HTTP."""


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


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
