from __future__ import annotations

import uuid
from abc import abstractmethod

from modules.identity_access.domain.entities.session import Session
from modules.identity_access.domain.value_objects.enums import SessionEndedReason
from shared_kernel.domain.repository import Repository


class SessionRepository(Repository[Session, uuid.UUID]):
    @abstractmethod
    async def end_all_active_for_user(self, user_id: uuid.UUID, reason: SessionEndedReason) -> None:
        """Usado por `reset-password` (`001-authentication.md`, linha 151 — toda sessão ativa é
        encerrada ao concluir o reset)."""
