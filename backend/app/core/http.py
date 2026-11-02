"""HTTP plumbing shared by every router: error mapping and CORS."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings
from .errors import AppError
from .i18n import translator


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
        locale = translator.negotiate(request.headers.get("accept-language"))
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.text(locale), "code": type(error).__name__, "key": error.key},
        )


def install_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
