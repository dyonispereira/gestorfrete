from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.audit.audit_reader import AuditTrailReader
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.financial_reversal_dto import FinancialReversalDTO
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_financial_reversal_repository import (
    SqlAlchemyFinancialReversalRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetFinancialReversalQuery(Query):
    actor: AuthenticatedActor
    financial_reversal_id: uuid.UUID


class GetFinancialReversalHandler(QueryHandler[GetFinancialReversalQuery, FinancialReversalDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetFinancialReversalQuery) -> FinancialReversalDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyFinancialReversalRepository(session)
            reversal = await repo.get_by_id(query.financial_reversal_id)
            if reversal is None:
                raise NotFoundError("FINANCIAL_REVERSAL_NOT_FOUND", "Estorno não encontrado.")
            actor = await AuditTrailReader().find_actor(
                session, tenant_id=query.actor.tenant_id, entidade_tipo="estornos_financeiros",
                entidade_id=reversal.id, acao="CRIACAO",
            )
        return FinancialReversalDTO.from_entity(reversal, criado_por=actor.ator_id if actor else None)
