from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.identity_access.domain.entities.permission import Permission
from modules.identity_access.domain.repositories.permission_repository import PermissionRepository
from modules.identity_access.infrastructure.persistence.models.identity_models import PermissionModel


def _to_entity(model: PermissionModel) -> Permission:
    return Permission(
        id=model.id, code=model.codigo, name=model.nome, module=model.modulo, created_at=model.criado_em
    )


class SqlAlchemyPermissionRepository(PermissionRepository):
    """Platform Reference Data (D046) — nunca filtra por tenant, mesma consulta para qualquer
    tenant (`005-permissions.md`)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Permission | None:
        model = await self._session.get(PermissionModel, id)
        return _to_entity(model) if model is not None else None

    async def get_by_codes(self, codes: list[str]) -> list[Permission]:
        if not codes:
            return []
        stmt = select(PermissionModel).where(PermissionModel.codigo.in_(codes))
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def get_by_ids(self, ids: frozenset[uuid.UUID]) -> list[Permission]:
        if not ids:
            return []
        stmt = select(PermissionModel).where(PermissionModel.id.in_(ids))
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def list_page(
        self, *, page: int, limit: int, module: str | None, search: str | None
    ) -> tuple[list[Permission], int]:
        stmt = select(PermissionModel)
        if module is not None:
            stmt = stmt.where(PermissionModel.modulo == module)
        if search is not None:
            like = f"%{search}%"
            stmt = stmt.where(PermissionModel.nome.ilike(like) | PermissionModel.codigo.ilike(like))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(PermissionModel.codigo).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total
