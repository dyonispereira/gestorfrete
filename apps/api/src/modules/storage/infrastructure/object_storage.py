from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import timedelta

from minio.error import S3Error

from core.storage.minio_client import get_minio_client

BUCKET_NAME = "gestorfrete-files"
UPLOAD_URL_EXPIRY = timedelta(minutes=15)
DOWNLOAD_URL_EXPIRY = timedelta(minutes=15)


def build_storage_key(tenant_id: uuid.UUID, file_id: uuid.UUID) -> str:
    """`{tenant_id}/{file_id}` — nunca o nome original (evita colisão/travessia de path); o nome
    original só existe como metadado (`arquivos.nome_original`), nunca na chave física."""

    return f"{tenant_id}/{file_id}"


async def ensure_bucket_exists() -> None:
    client = get_minio_client()

    def _ensure() -> None:
        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)

    await asyncio.to_thread(_ensure)


async def presigned_upload_url(storage_key: str) -> str:
    client = get_minio_client()
    return await asyncio.to_thread(
        client.presigned_put_object, BUCKET_NAME, storage_key, expires=UPLOAD_URL_EXPIRY
    )


async def presigned_download_url(storage_key: str) -> str:
    client = get_minio_client()
    return await asyncio.to_thread(
        client.presigned_get_object, BUCKET_NAME, storage_key, expires=DOWNLOAD_URL_EXPIRY
    )


async def stat_object(storage_key: str) -> int | None:
    """Retorna `tamanho_bytes` se o objeto existe no bucket, `None` caso contrário — usado por
    `commands/complete` para confirmar que o cliente realmente enviou o binário."""

    client = get_minio_client()

    def _stat() -> int | None:
        try:
            result = client.stat_object(BUCKET_NAME, storage_key)
            return result.size
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                return None
            raise

    return await asyncio.to_thread(_stat)


async def compute_object_hash(storage_key: str) -> str:
    """SHA-256 do objeto já enviado — o backend nunca vê o binário durante `POST /uploads` (o
    cliente envia direto ao Storage), então o hash só pode ser calculado lendo de volta, aqui, no
    momento de `commands/complete`."""

    client = get_minio_client()

    def _hash() -> str:
        response = client.get_object(BUCKET_NAME, storage_key)
        try:
            digest = hashlib.sha256()
            for chunk in response.stream(32 * 1024):
                digest.update(chunk)
            return digest.hexdigest()
        finally:
            response.close()
            response.release_conn()

    return await asyncio.to_thread(_hash)


async def upload_object_bytes(storage_key: str, data: bytes, content_type: str) -> None:
    """Usado por consumidores internos (`origin=GERADO_PELO_SISTEMA`, ex.: cofre de segredo HMAC de
    Webhook, D413) que não passam pelo fluxo de upload assinado do cliente — nunca chamado a partir
    de um endpoint HTTP público (D314: cliente sempre envia direto ao Storage)."""

    import io

    client = get_minio_client()

    def _put() -> None:
        client.put_object(BUCKET_NAME, storage_key, io.BytesIO(data), length=len(data), content_type=content_type)

    await asyncio.to_thread(_put)
