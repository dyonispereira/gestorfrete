from __future__ import annotations

from fastapi import APIRouter, Response, status

from core.cache.redis_client import check_redis_connection
from core.config.settings import get_settings
from core.database.session import check_database_connection
from core.messaging.rabbitmq_client import check_rabbitmq_connection
from core.storage.minio_client import check_storage_connection

health_router = APIRouter(tags=["Health"])
"""Technical endpoints, deliberately outside ``/api/v1`` and outside the
frozen business OpenAPI contract (D329/D332 — infrastructure endpoints are
the one explicit exception to "no endpoint without a contract entry").
"""


@health_router.get("/health")
async def health() -> dict[str, str]:
    """Coarse "is the process up" check — no dependency is verified here,
    only that the app can respond at all."""

    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@health_router.get("/health/live")
async def liveness() -> dict[str, str]:
    """Kubernetes-style liveness probe: never checks external dependencies —
    a down database must not make an orchestrator kill and restart a
    perfectly healthy process (that would just cause a crash loop)."""

    return {"status": "alive"}


@health_router.get("/health/ready")
async def readiness(response: Response) -> dict[str, object]:
    """Kubernetes-style readiness probe: checks every external dependency
    the app needs to actually serve traffic. Returns ``503`` the moment any
    one of them is down, with a per-dependency breakdown — never a bare
    boolean, so on-call can tell *which* dependency is the problem without
    reading logs first.

    Production Readiness Hardening, Parte 2 — ``rabbitmq`` só entra na conta de "pronto" quando
    ``RABBITMQ_ENABLED=true`` (default). O piloto roda com RabbitMQ desligado (nenhum
    publisher/consumidor real existe hoje) — sem essa condição, readiness ficaria permanentemente
    503 por uma dependência que nenhum fluxo de negócio de fato usa. Desligado, o check aparece
    como ``"disabled"`` no corpo da resposta (nunca omitido — quem olha o payload sempre vê
    explicitamente que RabbitMQ está desligado por configuração, não que o endpoint "esqueceu" dele)
    e nunca conta contra ``all_ready``."""

    settings = get_settings()
    checks: dict[str, bool | str] = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "rabbitmq": await check_rabbitmq_connection() if settings.rabbitmq_enabled else "disabled",
        "storage": await check_storage_connection(),
    }
    all_ready = all(value is True or value == "disabled" for value in checks.values())
    response.status_code = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if all_ready else "not_ready", "checks": checks}
