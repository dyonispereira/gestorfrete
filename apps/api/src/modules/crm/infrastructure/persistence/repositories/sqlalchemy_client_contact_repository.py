from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.crm.domain.entities.client_contact import ClientContact
from modules.crm.domain.repositories.client_contact_repository import ClientContactRepository
from modules.crm.infrastructure.persistence.models.client_contact_model import ClientContactModel


def _to_entity(model: ClientContactModel) -> ClientContact:
    return ClientContact(
        id=model.id,
        cliente_id=model.cliente_id,
        nome=model.nome,
        cargo=model.cargo,
        telefone=model.telefone,
        email=model.email,
        created_at=model.criado_em,
        updated_at=model.atualizado_em,
        deleted_at=model.excluido_em,
    )


class SqlAlchemyClientContactRepository(ClientContactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> ClientContact | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ClientContactModel).where(
            ClientContactModel.id == id,
            ClientContactModel.tenant_id == tenant_id,
            ClientContactModel.excluido_em.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_client(self, cliente_id: uuid.UUID) -> list[ClientContact]:
        tenant_id = get_current_tenant_id()
        stmt = select(ClientContactModel).where(
            ClientContactModel.tenant_id == tenant_id,
            ClientContactModel.cliente_id == cliente_id,
            ClientContactModel.excluido_em.is_(None),
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, contact: ClientContact) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ClientContactModel, contact.id)
        if model is None:
            model = ClientContactModel(id=contact.id, tenant_id=tenant_id, cliente_id=contact.cliente_id)
            self._session.add(model)
        model.nome = contact.nome
        model.cargo = contact.cargo
        model.telefone = contact.telefone
        model.email = contact.email
        model.criado_em = contact.created_at
        model.atualizado_em = contact.updated_at
        model.excluido_em = contact.deleted_at
        await self._session.flush()
