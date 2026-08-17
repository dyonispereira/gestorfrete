from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from core.audit.models import LogAuditoriaModel

Acao = Literal["CRIACAO", "ALTERACAO", "EXCLUSAO_LOGICA", "LOGIN", "LOGOUT", "TRANSICAO_STATUS"]
Origem = Literal["WEB", "MOBILE", "API", "SISTEMA"]


class AuditLogger:
    """D344 — auditoria acompanha mudanças críticas de identidade e autorização (e, no futuro,
    qualquer outro bounded context que precisar). Grava **na mesma sessão/transação** do
    `UnitOfWork` que já está em andamento — nunca abre sua própria conexão — para que o registro de
    auditoria nunca seja perdido mesmo que o barramento de eventos (RabbitMQ) esteja indisponível: é
    o caminho síncrono e garantido, complementar (nunca substituto) aos Domain Events que os
    agregados já gravam para consumo assíncrono por outros bounded contexts (`EVENT_BUS.md`).

    Nunca editado nem apagado depois de escrito (D001/D037/D109) — não existe método `update`/
    `delete` nesta classe, só `record`.
    """

    async def record(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        entidade_tipo: str,
        entidade_id: uuid.UUID,
        acao: Acao,
        ator_id: uuid.UUID | None,
        ator_nome_snapshot: str,
        origem: Origem = "API",
        dados_antes: dict[str, Any] | None = None,
        dados_depois: dict[str, Any] | None = None,
        motivo: str | None = None,
        id_correlacao: uuid.UUID | None = None,
    ) -> None:
        session.add(
            LogAuditoriaModel(
                id=uuid.uuid4(),
                data_hora=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                entidade_tipo=entidade_tipo,
                entidade_id=entidade_id,
                acao=acao,
                ator_id=ator_id,
                ator_nome_snapshot=ator_nome_snapshot,
                origem=origem,
                dados_antes=dados_antes,
                dados_depois=dados_depois,
                motivo=motivo,
                id_correlacao=id_correlacao or uuid.uuid4(),
            )
        )
