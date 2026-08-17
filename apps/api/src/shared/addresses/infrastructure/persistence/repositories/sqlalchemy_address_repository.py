from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from shared.addresses.domain.entities.address import Address
from shared.addresses.domain.repositories.address_repository import AddressRepository
from shared.addresses.domain.value_objects.address_type import AddressType
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared.addresses.infrastructure.persistence.models.address_model import AddressModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: AddressModel) -> Address:
    return Address(
        id=model.id,
        owner_type=OwnerType(model.entidade_tipo),
        owner_id=model.entidade_id,
        tipo=AddressType(model.tipo_endereco),
        logradouro=model.logradouro,
        numero=model.numero,
        complemento=model.complemento,
        bairro=model.bairro,
        cidade=model.cidade,
        uf=model.uf,
        cep=model.cep,
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyAddressRepository(AddressRepository):
    """Filtra por `tenant_id` do contexto corrente (D338/D339), como todo outro Repository deste
    projeto, além de `entidade_tipo`/`entidade_id` (o par dono, sempre resolvido pelo módulo
    chamador — nunca aceito de fora, `ADDRESS_IMPLEMENTATION.md`)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Address | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AddressModel).where(
            AddressModel.id == id,
            AddressModel.tenant_id == tenant_id,
            AddressModel.excluido_em.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_owner(self, owner_type: OwnerType, owner_id: uuid.UUID) -> list[Address]:
        tenant_id = get_current_tenant_id()
        stmt = select(AddressModel).where(
            AddressModel.tenant_id == tenant_id,
            AddressModel.entidade_tipo == owner_type.value,
            AddressModel.entidade_id == owner_id,
            AddressModel.excluido_em.is_(None),
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def has_principal(self, owner_type: OwnerType, owner_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(AddressModel.id).where(
            AddressModel.tenant_id == tenant_id,
            AddressModel.entidade_tipo == owner_type.value,
            AddressModel.entidade_id == owner_id,
            AddressModel.tipo_endereco == AddressType.PRINCIPAL.value,
            AddressModel.excluido_em.is_(None),
        )
        return (await self._session.execute(stmt)).first() is not None

    async def add(self, aggregate: Address) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(AddressModel, aggregate.id)
        if model is None:
            model = AddressModel(
                id=aggregate.id,
                tenant_id=tenant_id,
                entidade_tipo=aggregate.owner_type.value,
                entidade_id=aggregate.owner_id,
            )
            self._session.add(model)
        model.tipo_endereco = aggregate.tipo.value
        model.logradouro = aggregate.logradouro
        model.numero = aggregate.numero
        model.complemento = aggregate.complemento
        model.bairro = aggregate.bairro
        model.cidade = aggregate.cidade
        model.uf = aggregate.uf
        model.cep = aggregate.cep
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

    async def find(self, specification: Specification[Address]) -> list[Address]:
        raise NotImplementedError("Use list_for_owner — filtros de Address são resolvidos via SQL")
