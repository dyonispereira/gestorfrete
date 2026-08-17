from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.correction_letter_dto import CorrectionLetterDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_correction_letter_repository import (
    SqlAlchemyCorrectionLetterRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListCorrectionLettersQuery(Query):
    actor: AuthenticatedActor
    cte_id: uuid.UUID


class ListCorrectionLettersHandler(QueryHandler[ListCorrectionLettersQuery, list[CorrectionLetterDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListCorrectionLettersQuery) -> list[CorrectionLetterDTO]:
        async with self._session_factory() as session:
            cte_repo = SqlAlchemyCteRepository(session)
            if await cte_repo.get_by_id(query.cte_id) is None:
                raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")

            letter_repo = SqlAlchemyCorrectionLetterRepository(session)
            letters = await letter_repo.list_for_cte(query.cte_id)
        return [CorrectionLetterDTO.from_entity(letter) for letter in letters]
