from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.identity_access.domain.entities.role import Role
from modules.identity_access.domain.repositories.role_repository import RoleRepository
from modules.identity_access.infrastructure.persistence.models.identity_models import (
    RoleModel,
    papel_permissao,
    usuarios_papeis,
)
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: RoleModel, permission_ids: frozenset[uuid.UUID]) -> Role:
    return Role(
        id=model.id,
        codigo=model.codigo,
        nome=model.nome,
        descricao=model.descricao,
        permission_ids=permission_ids,
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _permission_ids_for(self, role_id: uuid.UUID) -> frozenset[uuid.UUID]:
        stmt = select(papel_permissao.c.permissao_id).where(papel_permissao.c.papel_id == role_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return frozenset(rows)

    async def get_by_id(self, id: uuid.UUID) -> Role | None:
        tenant_id = get_current_tenant_id()
        stmt = select(RoleModel).where(
            RoleModel.id == id, RoleModel.tenant_id == tenant_id, RoleModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return _to_entity(model, await self._permission_ids_for(model.id))

    async def get_many(self, ids: frozenset[uuid.UUID]) -> list[Role]:
        if not ids:
            return []
        tenant_id = get_current_tenant_id()
        stmt = select(RoleModel).where(
            RoleModel.id.in_(ids), RoleModel.tenant_id == tenant_id, RoleModel.excluido_em.is_(None)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m, await self._permission_ids_for(m.id)) for m in models]

    async def exists_with_name(self, nome: str, *, excluding_id: uuid.UUID | None = None) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(RoleModel.id).where(RoleModel.tenant_id == tenant_id, RoleModel.nome == nome)
        if excluding_id is not None:
            stmt = stmt.where(RoleModel.id != excluding_id)
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(self, *, page: int, limit: int, search: str | None) -> tuple[list[Role], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(RoleModel).where(RoleModel.tenant_id == tenant_id, RoleModel.excluido_em.is_(None))
        if search is not None:
            stmt = stmt.where(RoleModel.nome.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(RoleModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        roles = [_to_entity(m, await self._permission_ids_for(m.id)) for m in models]
        return roles, total

    async def is_assigned_to_any_user(self, role_id: uuid.UUID) -> bool:
        stmt = select(usuarios_papeis.c.usuario_id).where(usuarios_papeis.c.papel_id == role_id)
        return (await self._session.execute(stmt)).first() is not None

    async def add(self, aggregate: Role) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(RoleModel, aggregate.id)
        if model is None:
            model = RoleModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.nome = aggregate.nome
        model.descricao = aggregate.descricao
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

        current = await self._permission_ids_for(aggregate.id)
        to_remove = current - aggregate.permission_ids
        to_add = aggregate.permission_ids - current
        if to_remove:
            await self._session.execute(
                delete(papel_permissao).where(
                    papel_permissao.c.papel_id == aggregate.id,
                    papel_permissao.c.permissao_id.in_(to_remove),
                )
            )
        if to_add:
            now = datetime.now(timezone.utc)
            await self._session.execute(
                insert(papel_permissao),
                [
                    {"papel_id": aggregate.id, "permissao_id": permissao_id, "criado_em": now}
                    for permissao_id in to_add
                ],
            )

    async def find(self, specification: Specification[Role]) -> list[Role]:
        raise NotImplementedError("Use list_page — filtros de Role são resolvidos via SQL")
