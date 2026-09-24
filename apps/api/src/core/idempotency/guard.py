from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel

from core.exceptions.base import ConflictError
from core.idempotency.store import IdempotencyStore, fingerprint


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
    efeito colateral)."""

    if idempotency_key is None:
        result = await run()
        return status_code, result.model_dump(mode="json")

    store = IdempotencyStore()
    fp = fingerprint(method=method, path=path, payload=payload)

    existing = await store.get(tenant_id=tenant_id, idempotency_key=idempotency_key)
    if existing is not None:
        if existing.fingerprint != fp:
            raise ConflictError(
                "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH",
                "Idempotency-Key já usada para uma requisição com corpo diferente.",
            )
        if existing.response is not None:
            return existing.response.status_code, existing.response.body

    result = await run()
    body = result.model_dump(mode="json")
    await store.save(tenant_id=tenant_id, idempotency_key=idempotency_key, fingerprint=fp, status_code=status_code, body=body)
    return status_code, body
