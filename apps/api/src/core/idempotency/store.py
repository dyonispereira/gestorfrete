from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any

from core.cache.redis_client import get_redis_client

_TTL_SECONDS = 24 * 60 * 60


def fingerprint(*, method: str, path: str, payload: dict[str, Any]) -> str:
    """Inclui `method`+`path` no hash (não só o corpo) — a mesma chave reutilizada por engano em
    duas rotas diferentes produz `IDEMPOTENCY_KEY_PAYLOAD_MISMATCH` em vez de colidir
    silenciosamente, mesmo no caso raro de corpos coincidentes."""

    normalized = json.dumps({"method": method, "path": path, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StoredResponse:
    status_code: int
    body: dict[str, Any]


@dataclass(frozen=True)
class IdempotencyRecord:
    fingerprint: str
    response: StoredResponse | None
    """`None` enquanto a tentativa original ainda não terminou com sucesso — nunca grava um
    marcador "em voo" (`IDEMPOTENCY.md`, seção "Retry em falha"), então na prática hoje isto nunca
    fica `None` depois de `get()` encontrar um registro; o campo existe para deixar a leitura do
    JSON armazenado explícita em vez de assumir a forma do payload."""


class IdempotencyStore:
    """D211/`docs/api/IDEMPOTENCY.md` — Redis-backed. Chave: `idempotency:{tenant_id}:{key}`.
    Retenção 24h (`SETEX`, ponto de partida documentado, ajustável). Sem lock distribuído entre
    requisições concorrentes com a mesma chave — a garantia real de "nunca duas entidades" contra
    concorrência vem da constraint física/invariante de domínio de cada operação (D193-style,
    defesa em profundidade); esta camada resolve o caso prático dominante: duplo-clique e retry de
    rede sequencial, não uma corrida distribuída de dois requests simultâneos."""

    def __init__(self) -> None:
        self._redis = get_redis_client()

    @staticmethod
    def _redis_key(tenant_id: uuid.UUID, idempotency_key: str) -> str:
        return f"idempotency:{tenant_id}:{idempotency_key}"

    async def get(self, *, tenant_id: uuid.UUID, idempotency_key: str) -> IdempotencyRecord | None:
        raw = await self._redis.get(self._redis_key(tenant_id, idempotency_key))
        if raw is None:
            return None
        data = json.loads(raw)
        return IdempotencyRecord(
            fingerprint=data["fingerprint"],
            response=StoredResponse(status_code=data["status_code"], body=data["body"]),
        )

    async def save(
        self, *, tenant_id: uuid.UUID, idempotency_key: str, fingerprint: str, status_code: int, body: dict[str, Any]
    ) -> None:
        payload = json.dumps({"fingerprint": fingerprint, "status_code": status_code, "body": body}, default=str)
        await self._redis.set(self._redis_key(tenant_id, idempotency_key), payload, ex=_TTL_SECONDS)
