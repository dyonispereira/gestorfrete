from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.fleet.domain.entities.vehicle_document import VehicleDocument
from modules.fleet.domain.repositories.vehicle_document_repository import VehicleDocumentRepository
from modules.fleet.infrastructure.persistence.models.vehicle_document_model import VehicleDocumentModel


def _to_entity(model: VehicleDocumentModel) -> VehicleDocument:
    return VehicleDocument(
        id=model.id,
        veiculo_tracionador_id=model.veiculo_tracionador_id,
        tipo=model.tipo,
        numero=model.numero,
        data_validade=model.data_validade,
        arquivo_id=model.arquivo_id,
    )


class SqlAlchemyVehicleDocumentRepository(VehicleDocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> VehicleDocument | None:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleDocumentModel).where(
            VehicleDocumentModel.id == id, VehicleDocumentModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, veiculo_tracionador_id: uuid.UUID, page: int, limit: int, tipo: str | None, status: str | None
    ) -> tuple[list[VehicleDocument], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(VehicleDocumentModel).where(
            VehicleDocumentModel.tenant_id == tenant_id,
            VehicleDocumentModel.veiculo_tracionador_id == veiculo_tracionador_id,
        )
        if tipo is not None:
            stmt = stmt.where(VehicleDocumentModel.tipo == tipo)
        if status is not None:
            stmt = stmt.where(VehicleDocumentModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, document: VehicleDocument) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(VehicleDocumentModel, document.id)
        if model is None:
            model = VehicleDocumentModel(
                id=document.id, tenant_id=tenant_id, veiculo_tracionador_id=document.veiculo_tracionador_id
            )
            self._session.add(model)
        model.tipo = document.tipo
        model.numero = document.numero
        model.data_validade = document.data_validade
        model.status = document.status.value
        model.arquivo_id = document.arquivo_id
        await self._session.flush()
