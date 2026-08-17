from __future__ import annotations

import uuid

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from shared.collaboration.domain.entities.comment import Comment
from shared.collaboration.domain.repositories.comment_repository import CommentRepository
from shared.collaboration.infrastructure.persistence.models.comment_model import CommentModel


def _to_entity(model: CommentModel) -> Comment:
    return Comment(
        id=model.id,
        entidade_tipo=model.entidade_tipo,
        entidade_id=model.entidade_id,
        usuario_id=model.usuario_id,
        texto=model.texto,
        visivel_cliente=model.visivel_cliente,
        criado_em=model.criado_em,
    )


class SqlAlchemyCommentRepository(CommentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Comment | None:
        tenant_id = get_current_tenant_id()
        stmt = select(CommentModel).where(CommentModel.id == id, CommentModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_entity(self, entidade_tipo: str, entidade_id: uuid.UUID) -> list[Comment]:
        tenant_id = get_current_tenant_id()
        stmt = select(CommentModel).where(
            CommentModel.tenant_id == tenant_id,
            CommentModel.entidade_tipo == entidade_tipo,
            CommentModel.entidade_id == entidade_id,
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def create(self, comment: Comment) -> None:
        tenant_id = get_current_tenant_id()
        model = CommentModel(
            id=comment.id,
            tenant_id=tenant_id,
            entidade_tipo=comment.entidade_tipo,
            entidade_id=comment.entidade_id,
            usuario_id=comment.usuario_id,
            texto=comment.texto,
            visivel_cliente=comment.visivel_cliente,
            criado_em=comment.criado_em,
        )
        self._session.add(model)
        await self._session.flush()

    async def update(self, comment: Comment) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(CommentModel, comment.id)
        assert model is not None and model.tenant_id == tenant_id
        model.texto = comment.texto
        model.visivel_cliente = comment.visivel_cliente
        await self._session.flush()

    async def delete(self, id: uuid.UUID) -> None:
        tenant_id = get_current_tenant_id()
        stmt = sql_delete(CommentModel).where(CommentModel.id == id, CommentModel.tenant_id == tenant_id)
        await self._session.execute(stmt)
        await self._session.flush()
