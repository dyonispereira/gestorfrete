from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.notification_center.domain.entities.notification import Notification
from modules.notification_center.domain.repositories.notification_repository import NotificationRepository
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from modules.notification_center.domain.value_objects.notification_status import NotificationStatus
from modules.notification_center.infrastructure.persistence.models.notification_model import NotificationModel


def _to_entity(model: NotificationModel) -> Notification:
    return Notification(
        id=model.id, usuario_destinatario_id=model.usuario_destinatario_id, canal=NotificationChannel(model.canal),
        evento_origem_tipo=model.evento_origem_tipo, entidade_tipo=model.entidade_tipo, entidade_id=model.entidade_id,
        titulo=model.titulo, mensagem=model.mensagem, status=NotificationStatus(model.status),
        enviado_em=model.enviado_em, lido_em=model.lido_em,
    )


class SqlAlchemyNotificationRepository(NotificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Notification | None:
        tenant_id = get_current_tenant_id()
        stmt = select(NotificationModel).where(NotificationModel.id == id, NotificationModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page_for_user(
        self, usuario_id: uuid.UUID, *, page: int, limit: int, channel: str | None, status: str | None
    ) -> tuple[list[Notification], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(NotificationModel).where(
            NotificationModel.tenant_id == tenant_id, NotificationModel.usuario_destinatario_id == usuario_id
        )
        if channel is not None:
            stmt = stmt.where(NotificationModel.canal == channel)
        if status is not None:
            stmt = stmt.where(NotificationModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(NotificationModel.enviado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, notification: Notification) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(NotificationModel, notification.id)
        if model is None:
            model = NotificationModel(id=notification.id, tenant_id=tenant_id)
            self._session.add(model)
        model.usuario_destinatario_id = notification.usuario_destinatario_id
        model.canal = notification.canal.value
        model.evento_origem_tipo = notification.evento_origem_tipo
        model.entidade_tipo = notification.entidade_tipo
        model.entidade_id = notification.entidade_id
        model.titulo = notification.titulo
        model.mensagem = notification.mensagem
        model.status = notification.status.value
        model.enviado_em = notification.enviado_em
        model.lido_em = notification.lido_em
        await self._session.flush()
