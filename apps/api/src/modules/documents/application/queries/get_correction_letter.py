from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.correction_letter_dto import CorrectionLetterDTO
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_correction_letter_repository import (
    SqlAlchemyCorrectionLetterRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetCorrectionLetterQuery(Query):
    actor: AuthenticatedActor
    correction_letter_id: uuid.UUID


class GetCorrectionLetterHandler(QueryHandler[GetCorrectionLetterQuery, CorrectionLetterDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetCorrectionLetterQuery) -> CorrectionLetterDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyCorrectionLetterRepository(session)
            letter = await repo.get_by_id(query.correction_letter_id)
        if letter is None:
            raise NotFoundError("FISCAL_CORRECTION_LETTER_NOT_FOUND", "Carta de Correção não encontrada.")
        return CorrectionLetterDTO.from_entity(letter)
