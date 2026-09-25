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
    """`None` enquanto a tentativa original ainda não terminou — Pilot Hardening Final, Parte 6:
    `reserve()` agora grava exatamente esse marcador "em voo" antes de `run()` executar, fechando o
    gap de concorrência documentado antes aqui (duas requisições simultâneas com a mesma chave
    passavam pelo `get()` antes de qualquer uma gravar). `response=None` observado por `get()`
    significa "outra requisição está processando esta chave agora" — quem chama decide esperar."""


class IdempotencyStore:
    """D211/`docs/api/IDEMPOTENCY.md` — Redis-backed. Chave: `idempotency:{tenant_id}:{key}`.
    Retenção 24h (`SETEX`, ponto de partida documentado, ajustável).

    Pilot Hardening Final, Parte 6: `reserve()` usa `SET ... NX EX` — atômico no Redis, garante que
    só uma requisição concorrente consegue gravar a chave primeiro. As demais encontram a chave já
    reservada (`response=None`) e podem esperar pela resposta real em vez de correr para `run()`
    também. A garantia adicional de "nunca duas entidades" continua vindo da constraint física/
    invariante de domínio de cada operação (defesa em profundidade) — esta camada agora cobre tanto
    o caso prático dominante (duplo-clique e retry sequencial) quanto a corrida distribuída de dois
    requests simultâneos com a mesma chave."""

    def __init__(self) -> None:
        self._redis = get_redis_client()

    @staticmethod
    def _redis_key(tenant_id: uuid.UUID, idempotency_key: str) -> str:
        return f"idempotency:{tenant_id}:{idempotency_key}"

    async def reserve(self, *, tenant_id: uuid.UUID, idempotency_key: str, fingerprint: str) -> bool:
        """`SET NX EX` — grava o marcador "em voo" (`response=None`) só se a chave ainda não
        existir. Retorna `True` quando esta chamada é a dona da reserva (deve seguir para `run()`),
        `False` quando outra requisição já reservou ou concluiu esta chave primeiro."""

        payload = json.dumps({"fingerprint": fingerprint, "status_code": None, "body": None}, default=str)
        acquired = await self._redis.set(self._redis_key(tenant_id, idempotency_key), payload, nx=True, ex=_TTL_SECONDS)
        return bool(acquired)

    async def release(self, *, tenant_id: uuid.UUID, idempotency_key: str) -> None:
        """Libera a reserva quando `run()` falhou — sem isso, uma falha de negócio deixaria a chave
        presa em "em voo" até o TTL expirar, bloqueando qualquer retry legítimo por até 24h."""

        await self._redis.delete(self._redis_key(tenant_id, idempotency_key))

    async def get(self, *, tenant_id: uuid.UUID, idempotency_key: str) -> IdempotencyRecord | None:
        raw = await self._redis.get(self._redis_key(tenant_id, idempotency_key))
        if raw is None:
            return None
        data = json.loads(raw)
        response = None
        if data["status_code"] is not None:
            response = StoredResponse(status_code=data["status_code"], body=data["body"])
        return IdempotencyRecord(fingerprint=data["fingerprint"], response=response)

    async def save(
        self, *, tenant_id: uuid.UUID, idempotency_key: str, fingerprint: str, status_code: int, body: dict[str, Any]
    ) -> None:
        """Sobrescreve a reserva "em voo" com a resposta final — chamado só pela requisição que
        conseguiu `reserve()`, nunca precisa de `NX` aqui (é a dona da chave)."""

        payload = json.dumps({"fingerprint": fingerprint, "status_code": status_code, "body": body}, default=str)
        await self._redis.set(self._redis_key(tenant_id, idempotency_key), payload, ex=_TTL_SECONDS)
