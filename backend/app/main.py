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
from .services.scanning.router import router as scan_router
from .services.searches.router import router as searches_router
from .services.system.router import router as system_router
from .services.telegram.router import router as telegram_router
from .services.tenants.router import router as database_router

ROUTERS = (
    system_router, auth_router, searches_router, listings_router, database_router,
    export_router, telegram_router, billing_router, scan_router, admin_router,
)


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = settings or (container.settings if container else Settings.from_env())
    settings.validate()
    container = container or Container(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.scheduler_enabled:
            container.scheduler.start()
        yield
        container.scheduler.stop()

    app = FastAPI(title="Metravo API", version="1.0.0", lifespan=lifespan)
    app.state.container = container
    install_cors(app, settings)
    install_error_handlers(app)
    for router in ROUTERS:
        app.include_router(router)
    return app

