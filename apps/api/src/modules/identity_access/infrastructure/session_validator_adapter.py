from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)


class SqlAlchemySessionValidator:
    """Implementação real de `core.security.session_validation.SessionValidator` — registrada em
    `set_session_validator` durante o startup da aplicação (`modules.identity_access.wiring`).
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def is_session_valid(self, session_id: uuid.UUID) -> bool:
        async with self._session_factory() as session:
            repo = SqlAlchemySessionRepository(session)
            record = await repo.get_by_id(session_id)
        return record is not None and record.is_valid(datetime.now(timezone.utc))
