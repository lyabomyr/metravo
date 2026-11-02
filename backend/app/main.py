"""Application factory. Serve with ``uvicorn app.main:create_app --factory``."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import Settings
from .core.container import Container
from .core.http import install_cors, install_error_handlers
from .services.admin.router import router as admin_router
from .services.auth.router import router as auth_router
from .services.billing.router import router as billing_router
from .services.export.router import router as export_router
from .services.listings.router import router as listings_router
from .services.notifications.router import router as notifications_router
from .services.places.router import router as places_router
from .services.scanning.router import router as scan_router
from .services.searches.router import router as searches_router
from .services.system.router import router as system_router
from .services.telegram.router import router as telegram_router

ROUTERS = (
    system_router, auth_router, searches_router, listings_router, places_router,
    export_router, telegram_router, notifications_router, billing_router, scan_router, admin_router,
)


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = settings or (container.settings if container else Settings.from_env())
    settings.validate()
    container = container or Container(settings)
    logging.getLogger().addHandler(container.recent_logs)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.scheduler_enabled:
            container.scheduler.start()
        if settings.telegram_bot_token:
            container.background(container.bot_profile.publish)  # menu and descriptions, in every language
        yield
        container.scheduler.stop()

    app = FastAPI(title="Metravo API", version="1.0.0", lifespan=lifespan)
    app.state.container = container
    install_error_handlers(app)
    install_cors(app, settings)
    for router in ROUTERS:
        app.include_router(router)
    return app

