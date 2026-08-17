from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.cte import Cte
from modules.documents.domain.repositories.cte_repository import CteRepository
from modules.documents.domain.value_objects.cte_status import CteStatus
from modules.documents.infrastructure.persistence.models.cte_model import CteModel
from shared_kernel.domain.specification import Specification


def _to_entity(model: CteModel) -> Cte:
    return Cte(
        id=model.id, viagem_id=model.viagem_id, numero=model.numero, serie=model.serie,
        chave_acesso=model.chave_acesso, valor_servico=model.valor_servico, status=CteStatus(model.status),
        xml_arquivo_id=model.xml_arquivo_id, protocolo_sefaz=model.protocolo_sefaz,
        data_hora_autorizacao=model.data_hora_autorizacao, criado_em=model.criado_em,
        atualizado_em=model.atualizado_em,
    )


class SqlAlchemyCteRepository(CteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Cte | None:
        tenant_id = get_current_tenant_id()
        stmt = select(CteModel).where(CteModel.id == id, CteModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_protocolo_sefaz(self, protocolo_sefaz: str) -> Cte | None:
        tenant_id = get_current_tenant_id()
        stmt = select(CteModel).where(CteModel.tenant_id == tenant_id, CteModel.protocolo_sefaz == protocolo_sefaz)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_authorized_for_trip(self, viagem_id: uuid.UUID) -> list[Cte]:
        tenant_id = get_current_tenant_id()
        stmt = select(CteModel).where(
            CteModel.tenant_id == tenant_id, CteModel.viagem_id == viagem_id,
            CteModel.status == CteStatus.AUTORIZADO.value,
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def list_page(
        self, *, page: int, limit: int, viagem_id: uuid.UUID | None, status: str | None,
        serie: str | None, chave_acesso: str | None,
    ) -> tuple[list[Cte], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(CteModel).where(CteModel.tenant_id == tenant_id)
        if viagem_id is not None:
            stmt = stmt.where(CteModel.viagem_id == viagem_id)
        if status is not None:
            stmt = stmt.where(CteModel.status == status)
        if serie is not None:
            stmt = stmt.where(CteModel.serie == serie)
        if chave_acesso is not None:
            stmt = stmt.where(CteModel.chave_acesso == chave_acesso)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(CteModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Cte) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(CteModel, aggregate.id)
        if model is None:
            model = CteModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.viagem_id = aggregate.viagem_id
        model.numero = aggregate.numero
        model.serie = aggregate.serie
        model.chave_acesso = aggregate.chave_acesso
        model.valor_servico = aggregate.valor_servico
        model.status = aggregate.status.value
        model.xml_arquivo_id = aggregate.xml_arquivo_id
        model.protocolo_sefaz = aggregate.protocolo_sefaz
        model.data_hora_autorizacao = aggregate.data_hora_autorizacao
        model.criado_em = aggregate.criado_em
        model.atualizado_em = aggregate.atualizado_em
        await self._session.flush()

    async def find(self, specification: Specification[Cte]) -> list[Cte]:
        raise NotImplementedError("Use list_page — filtros de Cte são resolvidos via SQL")
