from __future__ import annotations

import uuid

from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from shared_kernel.domain.base_entity import BaseEntity


class ChannelPreference(BaseEntity[uuid.UUID]):
    """`preferencias_notificacao` — ausência de linha significa `habilitado=True` (default do
    contrato, `086-notifications.md`), nunca uma segunda leitura default hardcoded em dois
    lugares."""

    def __init__(self, id: uuid.UUID, *, usuario_id: uuid.UUID, canal: NotificationChannel, habilitado: bool) -> None:
        super().__init__(id)
        self.usuario_id = usuario_id
        self.canal = canal
        self.habilitado = habilitado

    @classmethod
    def create(cls, *, usuario_id: uuid.UUID, canal: NotificationChannel, habilitado: bool) -> "ChannelPreference":
        return cls(id=uuid.uuid4(), usuario_id=usuario_id, canal=canal, habilitado=habilitado)
