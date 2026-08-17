from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from core.config.settings import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped ``AsyncSession``.

    No ORM model is declared here — this module only wires the connection to
    PostgreSQL. Each bounded context owns its own models under
    ``modules/<context>/infrastructure/persistence/models``.
    """

    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def check_database_connection() -> bool:
    """Used by the ``/health/ready`` endpoint — returns ``False`` instead of
    raising so the health check can report a clean per-dependency result
    (``INFRASTRUCTURE.md``/``OBSERVABILITY.md``) rather than a stack trace.
    """

    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — deliberately broad: any failure means "not ready"
        return False


async def dispose_engine() -> None:
    """Called from the application lifespan on shutdown to close all pooled
    connections cleanly instead of letting the process exit hold them open.
    """

    engine = get_engine()
    await engine.dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
