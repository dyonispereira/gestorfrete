from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError
from modules.identity_access.domain.value_objects.enums import SessionEndedReason, SessionStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Session(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `identity_access` — implementação física de `Sessão de Acesso`
    (`docs/domain/010-administracao.md`, `sessoes_acesso`). **Nunca armazena permissão** — pedido
    explícito do usuário, também garantido pela própria tabela física, que não tem essa coluna."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        started_at: datetime,
        expires_at: datetime,
        ended_reason: SessionEndedReason | None,
        status: SessionStatus,
    ) -> None:
        super().__init__(id)
        self.user_id = user_id
        self.started_at = started_at
        self.expires_at = expires_at
        self.ended_reason = ended_reason
        self.status = status

    @classmethod
    def start(cls, *, user_id: uuid.UUID, started_at: datetime, expires_at: datetime) -> "Session":
        session = cls(
            id=uuid.uuid4(),
            user_id=user_id,
            started_at=started_at,
            expires_at=expires_at,
            ended_reason=None,
            status=SessionStatus.ATIVA,
        )
        return session

    def is_valid(self, now: datetime) -> bool:
        return self.status == SessionStatus.ATIVA and now < self.expires_at

    def end(self, reason: SessionEndedReason) -> None:
        if self.status != SessionStatus.ATIVA:
            raise ConflictError("IDENTITY_SESSION_ALREADY_ENDED", "Sessão já foi encerrada.")
        self.status = SessionStatus.ENCERRADA
        self.ended_reason = reason

    def extend(self, new_expires_at: datetime) -> None:
        """Usado por `POST /auth/refresh` — a mesma linha de Sessão avança sua janela de validade,
        nunca uma nova Sessão é criada para um refresh (`SESSION_IMPLEMENTATION.md`)."""

        if self.status != SessionStatus.ATIVA:
            raise ConflictError("IDENTITY_REFRESH_TOKEN_INVALID", "Sessão não está mais ativa.")
        self.expires_at = new_expires_at
