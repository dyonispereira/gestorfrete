from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.correction_letter import CorrectionLetter
from modules.documents.domain.repositories.correction_letter_repository import CorrectionLetterRepository
from modules.documents.infrastructure.persistence.models.correction_letter_model import CorrectionLetterModel


def _to_entity(model: CorrectionLetterModel) -> CorrectionLetter:
    return CorrectionLetter(
        id=model.id, cte_id=model.cte_id, numero_sequencial=model.numero_sequencial,
        texto_correcao=model.texto_correcao, xml_arquivo_id=model.xml_arquivo_id,
        data_hora_envio=model.data_hora_envio,
    )


class SqlAlchemyCorrectionLetterRepository(CorrectionLetterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> CorrectionLetter | None:
        tenant_id = get_current_tenant_id()
        stmt = select(CorrectionLetterModel).where(
            CorrectionLetterModel.id == id, CorrectionLetterModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_cte(self, cte_id: uuid.UUID) -> list[CorrectionLetter]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(CorrectionLetterModel)
            .where(CorrectionLetterModel.tenant_id == tenant_id, CorrectionLetterModel.cte_id == cte_id)
            .order_by(CorrectionLetterModel.numero_sequencial)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def next_sequence_number(self, cte_id: uuid.UUID) -> int:
        tenant_id = get_current_tenant_id()
        stmt = select(func.max(CorrectionLetterModel.numero_sequencial)).where(
            CorrectionLetterModel.tenant_id == tenant_id, CorrectionLetterModel.cte_id == cte_id
        )
        current_max = (await self._session.execute(stmt)).scalar_one_or_none()
        return (current_max or 0) + 1

    async def add(self, letter: CorrectionLetter) -> None:
        tenant_id = get_current_tenant_id()
        model = CorrectionLetterModel(
            id=letter.id, tenant_id=tenant_id, cte_id=letter.cte_id,
            numero_sequencial=letter.numero_sequencial, texto_correcao=letter.texto_correcao,
            xml_arquivo_id=letter.xml_arquivo_id, data_hora_envio=letter.data_hora_envio,
        )
        self._session.add(model)
        await self._session.flush()
