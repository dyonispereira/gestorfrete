from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.identity_access.domain.entities.user import User
from modules.identity_access.domain.repositories.user_repository import UserRepository
from modules.identity_access.domain.value_objects.enums import UserStatus
from modules.identity_access.infrastructure.persistence.models.identity_models import (
    UserModel,
    usuarios_papeis,
)
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: UserModel, role_ids: frozenset[uuid.UUID]) -> User:
    return User(
        id=model.id,
        codigo=model.codigo,
        nome=model.nome,
        email=model.email,
        senha_hash=model.senha_hash,
        status=UserStatus(model.status),
        driver_id=model.motorista_id,
        employee_id=model.funcionario_id,
        role_ids=role_ids,
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyUserRepository(UserRepository):
    """Todo método (exceto `get_by_email`, D208's exceção documentada para o login) filtra
    implicitamente pelo tenant do contexto corrente (`core.multitenancy.context`) — nenhum
    parâmetro `tenant_id` em nenhuma assinatura pública (`DOMAIN_LAYER.md`)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _role_ids_for(self, user_id: uuid.UUID) -> frozenset[uuid.UUID]:
        stmt = select(usuarios_papeis.c.papel_id).where(usuarios_papeis.c.usuario_id == user_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return frozenset(rows)

    async def get_by_id(self, id: uuid.UUID) -> User | None:
        tenant_id = get_current_tenant_id()
        stmt = select(UserModel).where(
            UserModel.id == id,
            UserModel.tenant_id == tenant_id,
            UserModel.excluido_em.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return _to_entity(model, await self._role_ids_for(model.id))

    async def get_by_email(self, email: str) -> tuple[User, uuid.UUID] | None:
        # Única exceção documentada a D208: login precisa descobrir o tenant a partir do e-mail,
        # antes de qualquer contexto de tenant existir — nunca usado fora do fluxo de autenticação.
        stmt = select(UserModel).where(UserModel.email == email, UserModel.excluido_em.is_(None))
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        role_ids = await self._role_ids_for(model.id)
        return _to_entity(model, role_ids), model.tenant_id

    async def exists_with_email(self, email: str) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(UserModel.id).where(UserModel.tenant_id == tenant_id, UserModel.email == email)
        return (await self._session.execute(stmt)).first() is not None

    async def get_by_driver_id_and_tenant(self, driver_id: uuid.UUID, tenant_id: uuid.UUID) -> User | None:
        stmt = select(UserModel).where(
            UserModel.motorista_id == driver_id, UserModel.tenant_id == tenant_id, UserModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return _to_entity(model, await self._role_ids_for(model.id))

    async def list_page(
        self, *, page: int, limit: int, status: str | None, role_id: uuid.UUID | None, search: str | None
    ) -> tuple[list[User], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(UserModel).where(
            UserModel.tenant_id == tenant_id, UserModel.excluido_em.is_(None)
        )
        if status is not None:
            stmt = stmt.where(UserModel.status == status)
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(UserModel.nome.ilike(like) | UserModel.email.ilike(like))
        if role_id is not None:
            stmt = stmt.join(usuarios_papeis, usuarios_papeis.c.usuario_id == UserModel.id).where(
                usuarios_papeis.c.papel_id == role_id
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(UserModel.nome).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        users = [_to_entity(m, await self._role_ids_for(m.id)) for m in models]
        return users, total

    async def count_active_admins(
        self, *, excluding_user_id: uuid.UUID, admin_role_ids: frozenset[uuid.UUID]
    ) -> int:
        if not admin_role_ids:
            return 0
        tenant_id = get_current_tenant_id()
        stmt = (
            select(func.count(func.distinct(UserModel.id)))
            .select_from(UserModel)
            .join(usuarios_papeis, usuarios_papeis.c.usuario_id == UserModel.id)
            .where(
                UserModel.tenant_id == tenant_id,
                UserModel.excluido_em.is_(None),
                UserModel.status == UserStatus.ATIVO.value,
                UserModel.id != excluding_user_id,
                usuarios_papeis.c.papel_id.in_(admin_role_ids),
            )
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def exists_active_linked_to_employee(self, employee_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(UserModel.id).where(
            UserModel.tenant_id == tenant_id,
            UserModel.funcionario_id == employee_id,
            UserModel.status == UserStatus.ATIVO.value,
            UserModel.excluido_em.is_(None),
        )
        return (await self._session.execute(stmt)).first() is not None

    async def add(self, aggregate: User) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(UserModel, aggregate.id)
        if model is None:
            model = UserModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.nome = aggregate.nome
        model.email = aggregate.email
        model.senha_hash = aggregate.senha_hash
        model.status = aggregate.status.value
        model.motorista_id = aggregate.driver_id
        model.funcionario_id = aggregate.employee_id
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        await self._session.flush()

        # `usuarios_papeis` é sempre recalculado para bater exatamente com `aggregate.role_ids`
        # (substituição completa, nunca incremental — `003-users.md`).
        current = await self._role_ids_for(aggregate.id)
        to_remove = current - aggregate.role_ids
        to_add = aggregate.role_ids - current
        if to_remove:
            await self._session.execute(
                delete(usuarios_papeis).where(
                    usuarios_papeis.c.usuario_id == aggregate.id,
                    usuarios_papeis.c.papel_id.in_(to_remove),
                )
            )
        if to_add:
            now = datetime.now(timezone.utc)
            await self._session.execute(
                insert(usuarios_papeis),
                [
                    {"usuario_id": aggregate.id, "papel_id": papel_id, "criado_em": now}
                    for papel_id in to_add
                ],
            )

    async def find(self, specification: Specification[User]) -> list[User]:
        raise NotImplementedError("Use list_page — filtros de User são resolvidos via SQL, não Specification em memória")
