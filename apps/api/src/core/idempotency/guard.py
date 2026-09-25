from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel

from core.exceptions.base import ConflictError
from core.idempotency.store import IdempotencyStore, StoredResponse, fingerprint

_POLL_INTERVAL_SECONDS = 0.1
_POLL_TIMEOUT_SECONDS = 5.0
_MAX_RESERVE_ATTEMPTS = 3
"""Só reentra no `reserve()` quando a chave foi liberada entre a nossa tentativa de reserva e a
leitura seguinte (a requisição dona falhou e chamou `release()` bem nesse intervalo) — uma corrida
rara, nunca o caminho comum. 3 tentativas é generoso para isso; não é um retry de negócio."""


async def with_idempotency(
    *,
    tenant_id: uuid.UUID,
    idempotency_key: str | None,
    method: str,
    path: str,
    payload: dict[str, Any],
    status_code: int,
    run: Callable[[], Awaitable[BaseModel]],
) -> tuple[int, dict[str, Any]]:
    """D211 — envolve o `run()` de um comando crítico (`docs/api/IDEMPOTENCY.md`). Sem
    `Idempotency-Key` no request, processa normalmente (o header é aceito, não exigido — exigi-lo
    quebraria todo cliente existente que ainda não o envia; a dedução real só acontece quando o
    header chega, o que já fecha o risco concreto de retry/duplo-clique visado nesta rodada).

    Só respostas de sucesso (o `run()` completou sem levantar) são retidas — uma falha de negócio
    (`DomainError`/`ConflictError`/etc.) propaga normalmente e nunca fica marcada como "resposta
    definitiva" aqui (simplificação documentada: `IDEMPOTENCY.md` também previa reter falhas de
    negócio `422`; esta primeira implementação cobre o caso que gera dano real — duplicar a
    entidade/efeito financeiro — não o caso de retry após erro, que já era seguro por não ter
    efeito colateral).

    Pilot Hardening Final, Parte 6 — protocolo reserva-então-resolve, atômico via `SET NX EX`
    (`IdempotencyStore.reserve`): a primeira requisição a reservar a chave é a única que chama
    `run()`; qualquer requisição concorrente com a mesma chave encontra a reserva e espera
    (`_poll_for_response`) em vez de correr para `run()` também — fecha o gap de concorrência que
    a implementação anterior (`GET` depois `SET`, sem atomicidade) deixava aberto."""

    if idempotency_key is None:
        result = await run()
        return status_code, result.model_dump(mode="json")

    store = IdempotencyStore()
    fp = fingerprint(method=method, path=path, payload=payload)

    for _ in range(_MAX_RESERVE_ATTEMPTS):
        reserved = await store.reserve(tenant_id=tenant_id, idempotency_key=idempotency_key, fingerprint=fp)
        if reserved:
            try:
                result = await run()
            except BaseException:
                await store.release(tenant_id=tenant_id, idempotency_key=idempotency_key)
                raise
            body = result.model_dump(mode="json")
            await store.save(
                tenant_id=tenant_id, idempotency_key=idempotency_key, fingerprint=fp,
                status_code=status_code, body=body,
            )
            return status_code, body

        record = await store.get(tenant_id=tenant_id, idempotency_key=idempotency_key)
        if record is None:
            continue  # liberada entre a tentativa de reserva e esta leitura — tenta reservar de novo

        if record.fingerprint != fp:
            raise ConflictError(
                "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH",
                "Idempotency-Key já usada para uma requisição com corpo diferente.",
            )
        if record.response is not None:
            return record.response.status_code, record.response.body

        polled = await _poll_for_response(store, tenant_id=tenant_id, idempotency_key=idempotency_key)
        if polled is not None:
            return polled.status_code, polled.body
        # `None`: a requisição dona falhou e liberou a chave durante a espera — tenta reservar.

    raise ConflictError(
        "IDEMPOTENCY_KEY_IN_PROGRESS",
        "Requisição com esta Idempotency-Key ainda está em processamento. Tente novamente.",
    )


async def _poll_for_response(
    store: IdempotencyStore, *, tenant_id: uuid.UUID, idempotency_key: str
) -> StoredResponse | None:
    """Espera limitada (100ms × até 5s) pela resposta de uma requisição concorrente que já reservou
    esta chave. Retorna a resposta pronta, `None` se a reserva foi liberada (a dona falhou — quem
    chamou deve tentar reservar de novo), ou levanta `IDEMPOTENCY_KEY_IN_PROGRESS` se o teto de
    espera for atingido sem a dona nunca terminar."""

    attempts = int(_POLL_TIMEOUT_SECONDS / _POLL_INTERVAL_SECONDS)
    for _ in range(attempts):
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        record = await store.get(tenant_id=tenant_id, idempotency_key=idempotency_key)
        if record is None:
            return None
        if record.response is not None:
            return record.response

    raise ConflictError(
        "IDEMPOTENCY_KEY_IN_PROGRESS",
        "Requisição com esta Idempotency-Key ainda está em processamento. Tente novamente.",
    )
