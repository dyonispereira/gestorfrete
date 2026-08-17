from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.drivers.domain.entities.driver_document import DriverDocument
from modules.drivers.domain.repositories.driver_document_repository import DriverDocumentRepository
from modules.drivers.domain.value_objects.cnh_category import CnhCategory
from modules.drivers.domain.value_objects.document_type import DocumentType
from modules.drivers.infrastructure.persistence.models.driver_model import DriverDocumentModel


def _to_entity(model: DriverDocumentModel) -> DriverDocument:
    return DriverDocument(
        id=model.id,
        motorista_id=model.motorista_id,
        tipo_documento=DocumentType(model.tipo_documento),
        numero=model.numero,
        categoria_cnh=CnhCategory(model.categoria_cnh) if model.categoria_cnh else None,
        data_validade=model.data_validade,
        arquivo_id=model.arquivo_id,
        created_at=model.criado_em,
        updated_at=model.atualizado_em,
    )


class SqlAlchemyDriverDocumentRepository(DriverDocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> DriverDocument | None:
        tenant_id = get_current_tenant_id()
        stmt = select(DriverDocumentModel).where(
            DriverDocumentModel.id == id, DriverDocumentModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_driver(self, motorista_id: uuid.UUID) -> list[DriverDocument]:
        tenant_id = get_current_tenant_id()
        stmt = select(DriverDocumentModel).where(
            DriverDocumentModel.tenant_id == tenant_id, DriverDocumentModel.motorista_id == motorista_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, document: DriverDocument) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(DriverDocumentModel, document.id)
        if model is None:
            model = DriverDocumentModel(id=document.id, tenant_id=tenant_id, motorista_id=document.motorista_id)
            self._session.add(model)
        model.tipo_documento = document.tipo_documento.value
        model.numero = document.numero
        model.categoria_cnh = document.categoria_cnh.value if document.categoria_cnh else None
        model.data_validade = document.data_validade
        model.arquivo_id = document.arquivo_id
        model.status = document.status.value
        model.criado_em = document.created_at
        model.atualizado_em = document.updated_at
        await self._session.flush()

    async def delete(self, document: DriverDocument) -> None:
        """`documentos_motorista` não tem `excluido_em` — `DELETE` real, não soft delete (mesma
        exceção documentada em `DriverDocumentModel`)."""

        await self._session.execute(delete(DriverDocumentModel).where(DriverDocumentModel.id == document.id))
