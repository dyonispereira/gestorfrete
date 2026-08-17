from __future__ import annotations

import asyncio
from functools import lru_cache

from minio import Minio

from core.config.settings import get_settings


@lru_cache
def get_minio_client() -> Minio:
    """Returns the S3-compatible client used by the ``documents`` bounded
    context to store fiscal documents and other file attachments. No bucket
    is created here — that belongs to that module's infrastructure layer.
    """

    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


async def check_storage_connection() -> bool:
    """Used by ``/health/ready`` — the ``minio`` SDK is synchronous, so the
    call is offloaded to a thread to avoid blocking the event loop. Returns
    ``False`` instead of raising, same contract as the other health checks.
    """

    try:
        client = get_minio_client()
        await asyncio.to_thread(client.list_buckets)
        return True
    except Exception:  # noqa: BLE001 — any failure means "not ready"
        return False
