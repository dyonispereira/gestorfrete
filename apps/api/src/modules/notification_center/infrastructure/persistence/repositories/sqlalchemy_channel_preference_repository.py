from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.notification_center.domain.entities.channel_preference import ChannelPreference
from modules.notification_center.domain.repositories.channel_preference_repository import (
    ChannelPreferenceRepository,
)
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from modules.notification_center.infrastructure.persistence.models.channel_preference_model import (
    ChannelPreferenceModel,
)


def _to_entity(model: ChannelPreferenceModel) -> ChannelPreference:
    return ChannelPreference(
        id=model.id, usuario_id=model.usuario_id, canal=NotificationChannel(model.canal), habilitado=model.habilitado
    )


class SqlAlchemyChannelPreferenceRepository(ChannelPreferenceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, usuario_id: uuid.UUID, canal: NotificationChannel) -> ChannelPreference | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ChannelPreferenceModel).where(
            ChannelPreferenceModel.tenant_id == tenant_id, ChannelPreferenceModel.usuario_id == usuario_id,
            ChannelPreferenceModel.canal == canal.value,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_user(self, usuario_id: uuid.UUID) -> list[ChannelPreference]:
        tenant_id = get_current_tenant_id()
        stmt = select(ChannelPreferenceModel).where(
            ChannelPreferenceModel.tenant_id == tenant_id, ChannelPreferenceModel.usuario_id == usuario_id
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, preference: ChannelPreference) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(ChannelPreferenceModel, preference.id)
        if model is None:
            model = ChannelPreferenceModel(id=preference.id, tenant_id=tenant_id)
            self._session.add(model)
        model.usuario_id = preference.usuario_id
        model.canal = preference.canal.value
        model.habilitado = preference.habilitado
        await self._session.flush()
