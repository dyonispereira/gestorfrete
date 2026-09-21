from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit.models import LogAuditoriaModel


@dataclass(frozen=True)
class AuditActorSnapshot:
    ator_id: uuid.UUID | None
    ator_nome_snapshot: str
    data_hora: datetime


class AuditTrailReader:
    """Read-side simétrico ao `AuditLogger` (que só grava, D344) — consulta pontual de
    `logs_auditoria` por entidade+ação. Existe para casos como `FinancialReversal` (Lote
    Financeiro, Parte 2.1): a entidade deliberadamente não tem `AuditMetadata`/`ator_id` próprio
    (D266 — Estorno é um registro paralelo minimalista), mas a trilha transversal já captura quem
    criou cada um via `AuditLogger.record(acao="CRIACAO", ator_id=...)`. Não é um módulo de consulta
    de auditoria completo — `modules/audit` continua só scaffolding — isto é só o necessário para
    responder "quem fez isto" pontualmente, sem duplicar `ator_id` em cada entidade que perguntar.
    """

    async def find_actor(
        self, session: AsyncSession, *, tenant_id: uuid.UUID, entidade_tipo: str, entidade_id: uuid.UUID, acao: str,
    ) -> AuditActorSnapshot | None:
        stmt = (
            select(LogAuditoriaModel.ator_id, LogAuditoriaModel.ator_nome_snapshot, LogAuditoriaModel.data_hora)
            .where(
                LogAuditoriaModel.tenant_id == tenant_id, LogAuditoriaModel.entidade_tipo == entidade_tipo,
                LogAuditoriaModel.entidade_id == entidade_id, LogAuditoriaModel.acao == acao,
            )
            .order_by(LogAuditoriaModel.data_hora.asc())
            .limit(1)
        )
        row = (await session.execute(stmt)).first()
        if row is None:
            return None
        return AuditActorSnapshot(ator_id=row[0], ator_nome_snapshot=row[1], data_hora=row[2])

    async def find_actors_batch(
        self, session: AsyncSession, *, tenant_id: uuid.UUID, entidade_tipo: str,
        entidade_ids: list[uuid.UUID], acao: str,
    ) -> dict[uuid.UUID, AuditActorSnapshot]:
        """Evita N+1 numa listagem paginada — uma query para todas as entidades da página."""

        if not entidade_ids:
            return {}
        stmt = (
            select(
                LogAuditoriaModel.entidade_id, LogAuditoriaModel.ator_id, LogAuditoriaModel.ator_nome_snapshot,
                LogAuditoriaModel.data_hora,
            )
            .where(
                LogAuditoriaModel.tenant_id == tenant_id, LogAuditoriaModel.entidade_tipo == entidade_tipo,
                LogAuditoriaModel.entidade_id.in_(entidade_ids), LogAuditoriaModel.acao == acao,
            )
            .order_by(LogAuditoriaModel.data_hora.asc())
        )
        result: dict[uuid.UUID, AuditActorSnapshot] = {}
        for entidade_id, ator_id, ator_nome_snapshot, data_hora in (await session.execute(stmt)).all():
            if entidade_id not in result:  # primeira ocorrência = mais antiga (order_by asc)
                result[entidade_id] = AuditActorSnapshot(
                    ator_id=ator_id, ator_nome_snapshot=ator_nome_snapshot, data_hora=data_hora
                )
        return result
