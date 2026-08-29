from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.maintenance.domain.entities.aprovacao_custo import AprovacaoCusto
from modules.maintenance.domain.repositories.aprovacao_custo_repository import AprovacaoCustoRepository
from modules.maintenance.domain.value_objects.aprovacao_custo_decisao import AprovacaoCustoDecisao
from modules.maintenance.infrastructure.persistence.models.aprovacao_custo_model import AprovacaoCustoModel


def _to_entity(model: AprovacaoCustoModel) -> AprovacaoCusto:
    return AprovacaoCusto(
        id=model.id, ordem_servico_id=model.ordem_servico_id, nivel=model.nivel,
        decisao=AprovacaoCustoDecisao(model.decisao), justificativa=model.justificativa, ator_id=model.ator_id,
        data_hora=model.data_hora,
    )


class SqlAlchemyAprovacaoCustoRepository(AprovacaoCustoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, aprovacao: AprovacaoCusto) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            AprovacaoCustoModel(
                id=aprovacao.id, tenant_id=tenant_id, ordem_servico_id=aprovacao.ordem_servico_id,
                nivel=aprovacao.nivel, decisao=aprovacao.decisao.value, justificativa=aprovacao.justificativa,
                ator_id=aprovacao.ator_id, data_hora=aprovacao.data_hora,
            )
        )
        await self._session.flush()

    async def list_for_ordem_servico(self, ordem_servico_id: uuid.UUID) -> list[AprovacaoCusto]:
        tenant_id = get_current_tenant_id()
        stmt = select(AprovacaoCustoModel).where(
            AprovacaoCustoModel.tenant_id == tenant_id, AprovacaoCustoModel.ordem_servico_id == ordem_servico_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]
