from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.mobile.application.dtos.digital_signature_dto import DigitalSignatureDTO
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_digital_signature_repository import (
    SqlAlchemyDigitalSignatureRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetSignatureQuery(Query):
    actor: AuthenticatedActor
    signature_id: uuid.UUID


class GetSignatureHandler(QueryHandler[GetSignatureQuery, DigitalSignatureDTO]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetSignatureQuery) -> DigitalSignatureDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyDigitalSignatureRepository(session)
            signature = await repo.get_by_id(query.signature_id)
        if signature is None:
            raise NotFoundError("MOBILE_SIGNATURE_NOT_FOUND", "Assinatura Digital não encontrada.")
        return DigitalSignatureDTO.from_entity(signature)
