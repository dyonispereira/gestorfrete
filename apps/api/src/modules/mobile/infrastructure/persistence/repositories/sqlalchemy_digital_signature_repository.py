from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.mobile.domain.entities.digital_signature import DigitalSignature
from modules.mobile.domain.repositories.digital_signature_repository import DigitalSignatureRepository
from modules.mobile.domain.value_objects.signatory_role import SignatoryRole
from modules.mobile.domain.value_objects.signature_document_type import SignatureDocumentType
from modules.mobile.infrastructure.persistence.models.digital_signature_model import DigitalSignatureModel


def _to_entity(model: DigitalSignatureModel) -> DigitalSignature:
    return DigitalSignature(
        id=model.id, documento_tipo=SignatureDocumentType(model.documento_tipo), documento_id=model.documento_id,
        papel_signatario=SignatoryRole(model.papel_signatario),
        nome_signatario_informado=model.nome_signatario_informado, arquivo_id=model.arquivo_id,
        data_hora_captura=model.capturado_em, data_hora_recebimento=model.recebido_em,
    )


class SqlAlchemyDigitalSignatureRepository(DigitalSignatureRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> DigitalSignature | None:
        tenant_id = get_current_tenant_id()
        stmt = select(DigitalSignatureModel).where(
            DigitalSignatureModel.id == id, DigitalSignatureModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, signature: DigitalSignature) -> None:
        tenant_id = get_current_tenant_id()
        self._session.add(
            DigitalSignatureModel(
                id=signature.id, tenant_id=tenant_id, documento_tipo=signature.documento_tipo.value,
                documento_id=signature.documento_id, papel_signatario=signature.papel_signatario.value,
                nome_signatario_informado=signature.nome_signatario_informado, arquivo_id=signature.arquivo_id,
                capturado_em=signature.data_hora_captura, recebido_em=signature.data_hora_recebimento,
            )
        )
        await self._session.flush()

    async def list_page(
        self, *, page: int, limit: int, document_type: str | None, document_id: uuid.UUID | None
    ) -> tuple[list[DigitalSignature], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(DigitalSignatureModel).where(DigitalSignatureModel.tenant_id == tenant_id)
        if document_type is not None:
            stmt = stmt.where(DigitalSignatureModel.documento_tipo == document_type)
        if document_id is not None:
            stmt = stmt.where(DigitalSignatureModel.documento_id == document_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(DigitalSignatureModel.capturado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total
