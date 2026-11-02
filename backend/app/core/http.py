"""HTTP plumbing shared by every router: error mapping and CORS."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings
from .errors import AppError
from .i18n import translator

log = logging.getLogger("app.http")


def _error_response(request: Request, error: AppError) -> JSONResponse:
    locale = translator.negotiate(request.headers.get("accept-language"))
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.text(locale), "code": type(error).__name__, "key": error.key},
    )


class Unexpected(AppError):
    status_code = 500


def install_error_handlers(app: FastAPI) -> None:
    """Install before ``install_cors``.

    FastAPI answers an uncaught exception outside every middleware, so the
    answer has no CORS headers and the browser reports it as a network
    failure. Catching it here, inside CORS, lets the site show what happened.
    """

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
        return _error_response(request, error)

    @app.middleware("http")
    async def handle_crash(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            log.exception("%s %s crashed", request.method, request.url.path)
            return _error_response(request, Unexpected("errors.unexpected"))


def install_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
