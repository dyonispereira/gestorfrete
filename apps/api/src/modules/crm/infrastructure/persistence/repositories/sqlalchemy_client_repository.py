from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.crm.domain.entities.client import Client
from modules.crm.domain.repositories.client_repository import ClientRepository
from modules.crm.domain.value_objects.client_status import ClientStatus
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: ClientModel) -> Client:
    return Client(
        id=model.id,
        codigo=model.codigo,
        razao_social=model.razao_social,
        nome_fantasia=model.nome_fantasia,
        document=model.cnpj_cpf,
        telefone=model.telefone,
        email=model.email,
        status=ClientStatus(model.status),
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyClientRepository(ClientRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Client | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ClientModel).where(
            ClientModel.id == id, ClientModel.tenant_id == tenant_id, ClientModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_document(self, document: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(ClientModel.id).where(ClientModel.tenant_id == tenant_id, ClientModel.cnpj_cpf == document)
        if excluding_id is not None:
            stmt = stmt.where(ClientModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        document: str | None,
        search: str | None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> tuple[list[Client], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(ClientModel).where(ClientModel.tenant_id == tenant_id, ClientModel.excluido_em.is_(None))
        if status is not None:
            stmt = stmt.where(ClientModel.status == status)
        if document is not None:
            stmt = stmt.where(ClientModel.cnpj_cpf == document)
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(ClientModel.razao_social.ilike(like) | ClientModel.nome_fantasia.ilike(like))
        if created_from is not None:
            stmt = stmt.where(ClientModel.criado_em >= created_from)
        if created_to is not None:
            stmt = stmt.where(ClientModel.criado_em <= created_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(ClientModel.razao_social).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Client) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ClientModel, aggregate.id)
        if model is None:
            model = ClientModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.razao_social = aggregate.razao_social
        model.nome_fantasia = aggregate.nome_fantasia
        model.cnpj_cpf = aggregate.document
        model.telefone = aggregate.telefone
        model.email = aggregate.email
        model.status = aggregate.status.value
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[Client]) -> list[Client]:
        raise NotImplementedError("Use list_page — filtros de Client são resolvidos via SQL")
