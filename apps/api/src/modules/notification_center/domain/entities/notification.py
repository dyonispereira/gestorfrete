from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from modules.notification_center.domain.value_objects.notification_status import NotificationStatus
from shared_kernel.domain.base_entity import BaseEntity


class Notification(BaseEntity[uuid.UUID]):
    """`notificacoes` (D320/D323) — sempre efeito colateral de um evento de domínio já publicado,
    nunca a origem de uma nova decisão (`086-notifications.md`). Nasce só via `NotificationDispatcher`
    interno, nunca `POST` direto."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        usuario_destinatario_id: uuid.UUID,
        canal: NotificationChannel,
        evento_origem_tipo: str,
        entidade_tipo: str | None,
        entidade_id: uuid.UUID | None,
        titulo: str,
        mensagem: str,
        status: NotificationStatus,
        enviado_em: datetime,
        lido_em: datetime | None,
    ) -> None:
        super().__init__(id)
        self.usuario_destinatario_id = usuario_destinatario_id
        self.canal = canal
        self.evento_origem_tipo = evento_origem_tipo
        self.entidade_tipo = entidade_tipo
        self.entidade_id = entidade_id
        self.titulo = titulo
        self.mensagem = mensagem
        self.status = status
        self.enviado_em = enviado_em
        self.lido_em = lido_em

    @classmethod
    def dispatch(
        cls,
        *,
        usuario_destinatario_id: uuid.UUID,
        canal: NotificationChannel,
        evento_origem_tipo: str,
        entidade_tipo: str | None,
        entidade_id: uuid.UUID | None,
        titulo: str,
        mensagem: str,
        now: datetime,
    ) -> "Notification":
        return cls(
            id=uuid.uuid4(), usuario_destinatario_id=usuario_destinatario_id, canal=canal,
            evento_origem_tipo=evento_origem_tipo, entidade_tipo=entidade_tipo, entidade_id=entidade_id,
            titulo=titulo, mensagem=mensagem, status=NotificationStatus.NAO_LIDA, enviado_em=now, lido_em=None,
        )

    def mark_read(self, *, now: datetime) -> None:
        if self.status == NotificationStatus.LIDA:
            raise ConflictError("NOTIFICATION_ALREADY_READ", "Notificação já está lida.")
        self.status = NotificationStatus.LIDA
        self.lido_em = now
