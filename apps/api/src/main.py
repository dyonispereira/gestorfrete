from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config.settings import get_settings
from core.database.session import dispose_engine
from core.exceptions.handlers import register_exception_handlers
from core.messaging.rabbitmq_client import close_rabbitmq_connection
from core.observability.logging import configure_logging
from interfaces.api.health import health_router
from interfaces.api.v1.router import api_router_v1
from interfaces.middlewares.request_context import RequestContextMiddleware
from modules.identity_access import wiring as identity_access_wiring


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Connections to PostgreSQL/Redis/RabbitMQ/MinIO are established lazily
    (on first real use, or when ``/health/ready`` probes them) rather than
    eagerly here — a dependency that takes a few extra seconds to become
    reachable must never crash-loop the API process. ``depends_on:
    condition: service_healthy`` in ``docker-compose.yml`` already sequences
    container startup; ``/health/ready`` is the authoritative proof that
    every dependency is actually reachable once the process is up.
    """

    yield
    await dispose_engine()
    await close_rabbitmq_connection()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    identity_access_wiring.register()
    register_exception_handlers(app)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(api_router_v1)

    return app


app = create_app()
