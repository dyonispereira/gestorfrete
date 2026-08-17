from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.mdfe import Mdfe
from modules.documents.domain.repositories.mdfe_repository import MdfeRepository
from modules.documents.domain.value_objects.mdfe_status import MdfeStatus
from modules.documents.infrastructure.persistence.models.mdfe_model import MdfeCteModel, MdfeModel
from shared_kernel.domain.specification import Specification


def _to_entity(model: MdfeModel) -> Mdfe:
    return Mdfe(
        id=model.id, viagem_id=model.viagem_id, numero=model.numero, serie=model.serie,
        chave_acesso=model.chave_acesso, status=MdfeStatus(model.status), xml_arquivo_id=model.xml_arquivo_id,
        protocolo_sefaz=model.protocolo_sefaz, data_hora_encerramento=model.data_hora_encerramento,
    )


class SqlAlchemyMdfeRepository(MdfeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Mdfe | None:
        tenant_id = get_current_tenant_id()
        stmt = select(MdfeModel).where(MdfeModel.id == id, MdfeModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_protocolo_sefaz(self, protocolo_sefaz: str) -> Mdfe | None:
        tenant_id = get_current_tenant_id()
        stmt = select(MdfeModel).where(MdfeModel.tenant_id == tenant_id, MdfeModel.protocolo_sefaz == protocolo_sefaz)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, viagem_id: uuid.UUID | None, status: str | None, serie: str | None,
    ) -> tuple[list[Mdfe], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(MdfeModel).where(MdfeModel.tenant_id == tenant_id)
        if viagem_id is not None:
            stmt = stmt.where(MdfeModel.viagem_id == viagem_id)
        if status is not None:
            stmt = stmt.where(MdfeModel.status == status)
        if serie is not None:
            stmt = stmt.where(MdfeModel.serie == serie)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(MdfeModel.id.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add_cte_link(self, mdfe_id: uuid.UUID, cte_id: uuid.UUID) -> None:
        self._session.add(MdfeCteModel(mdfe_id=mdfe_id, cte_id=cte_id))
        await self._session.flush()

    async def list_cte_ids(self, mdfe_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(MdfeCteModel.cte_id).where(MdfeCteModel.mdfe_id == mdfe_id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def add(self, aggregate: Mdfe) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(MdfeModel, aggregate.id)
        if model is None:
            model = MdfeModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.viagem_id = aggregate.viagem_id
        model.numero = aggregate.numero
        model.serie = aggregate.serie
        model.chave_acesso = aggregate.chave_acesso
        model.status = aggregate.status.value
        model.xml_arquivo_id = aggregate.xml_arquivo_id
        model.protocolo_sefaz = aggregate.protocolo_sefaz
        model.data_hora_encerramento = aggregate.data_hora_encerramento
        await self._session.flush()

    async def find(self, specification: Specification[Mdfe]) -> list[Mdfe]:
        raise NotImplementedError("Use list_page — filtros de Mdfe são resolvidos via SQL")
