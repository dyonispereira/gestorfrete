from __future__ import annotations

import uuid

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from shared.collaboration.domain.entities.attachment import Attachment
from shared.collaboration.domain.repositories.attachment_repository import AttachmentRepository
from shared.collaboration.infrastructure.persistence.models.attachment_model import AttachmentModel


def _to_entity(model: AttachmentModel) -> Attachment:
    return Attachment(
        id=model.id,
        entidade_tipo=model.entidade_tipo,
        entidade_id=model.entidade_id,
        tipo_anexo=model.tipo_anexo,
        arquivo_id=model.arquivo_id,
        descricao=model.descricao,
        criado_em=model.criado_em,
        criado_por=model.criado_por,
    )


class SqlAlchemyAttachmentRepository(AttachmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Attachment | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AttachmentModel).where(AttachmentModel.id == id, AttachmentModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_entity(self, entidade_tipo: str, entidade_id: uuid.UUID) -> list[Attachment]:
        tenant_id = get_current_tenant_id()
        stmt = select(AttachmentModel).where(
            AttachmentModel.tenant_id == tenant_id,
            AttachmentModel.entidade_tipo == entidade_tipo,
            AttachmentModel.entidade_id == entidade_id,
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def count_by_file_id(self, file_id: uuid.UUID) -> int:
        tenant_id = get_current_tenant_id()
        stmt = select(func.count()).select_from(AttachmentModel).where(
            AttachmentModel.tenant_id == tenant_id, AttachmentModel.arquivo_id == file_id
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def create(self, attachment: Attachment) -> None:
        tenant_id = get_current_tenant_id()
        model = AttachmentModel(
            id=attachment.id,
            tenant_id=tenant_id,
            entidade_tipo=attachment.entidade_tipo,
            entidade_id=attachment.entidade_id,
            tipo_anexo=attachment.tipo_anexo,
            arquivo_id=attachment.arquivo_id,
            descricao=attachment.descricao,
            criado_em=attachment.criado_em,
            criado_por=attachment.criado_por,
        )
        self._session.add(model)
        await self._session.flush()

    async def delete(self, id: uuid.UUID) -> None:
        tenant_id = get_current_tenant_id()
        stmt = sql_delete(AttachmentModel).where(AttachmentModel.id == id, AttachmentModel.tenant_id == tenant_id)
        await self._session.execute(stmt)
        await self._session.flush()
