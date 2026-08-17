from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.fiscal_event import FiscalEvent
from modules.documents.domain.repositories.fiscal_event_repository import FiscalEventRepository
from modules.documents.domain.value_objects.fiscal_event_document_type import FiscalEventDocumentType
from modules.documents.domain.value_objects.fiscal_event_result import FiscalEventResult
from modules.documents.domain.value_objects.fiscal_event_type import FiscalEventType
from modules.documents.infrastructure.persistence.models.fiscal_event_model import FiscalEventModel
from shared_kernel.domain.specification import Specification


def _to_entity(model: FiscalEventModel) -> FiscalEvent:
    return FiscalEvent(
        id=model.id, documento_tipo=FiscalEventDocumentType(model.documento_tipo), documento_id=model.documento_id,
        tipo_evento=FiscalEventType(model.tipo_evento), payload_arquivo_id=model.payload_arquivo_id,
        protocolo_externo=model.protocolo_externo, data_hora_inicio=model.data_hora_inicio,
        data_hora_fim=model.data_hora_fim, duracao_ms=model.duracao_ms, numero_tentativa=model.numero_tentativa,
        resultado=FiscalEventResult(model.resultado) if model.resultado is not None else None, origem=model.origem,
    )


class SqlAlchemyFiscalEventRepository(FiscalEventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> FiscalEvent | None:
        tenant_id = get_current_tenant_id()
        stmt = select(FiscalEventModel).where(FiscalEventModel.id == id, FiscalEventModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_with_protocol(
        self, *, documento_tipo: str, documento_id: uuid.UUID, protocolo_externo: str
    ) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(FiscalEventModel.id).where(
            FiscalEventModel.tenant_id == tenant_id, FiscalEventModel.documento_tipo == documento_tipo,
            FiscalEventModel.documento_id == documento_id, FiscalEventModel.protocolo_externo == protocolo_externo,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def list_page(
        self,
        *,
        cursor_data_hora: datetime | None,
        cursor_id: uuid.UUID | None,
        limit: int,
        documento_tipo: str | None,
        documento_id: uuid.UUID | None,
        protocolo_externo: str | None,
        started_at_from: datetime | None,
        started_at_to: datetime | None,
        resultado: str | None,
        origem: str | None,
        numero_tentativa: int | None,
    ) -> list[FiscalEvent]:
        tenant_id = get_current_tenant_id()
        stmt = select(FiscalEventModel).where(FiscalEventModel.tenant_id == tenant_id)
        if documento_tipo is not None:
            stmt = stmt.where(FiscalEventModel.documento_tipo == documento_tipo)
        if documento_id is not None:
            stmt = stmt.where(FiscalEventModel.documento_id == documento_id)
        if protocolo_externo is not None:
            stmt = stmt.where(FiscalEventModel.protocolo_externo == protocolo_externo)
        if started_at_from is not None:
            stmt = stmt.where(FiscalEventModel.data_hora_inicio >= started_at_from)
        if started_at_to is not None:
            stmt = stmt.where(FiscalEventModel.data_hora_inicio <= started_at_to)
        if resultado is not None:
            stmt = stmt.where(FiscalEventModel.resultado == resultado)
        if origem is not None:
            stmt = stmt.where(FiscalEventModel.origem == origem)
        if numero_tentativa is not None:
            stmt = stmt.where(FiscalEventModel.numero_tentativa == numero_tentativa)
        if cursor_data_hora is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    FiscalEventModel.data_hora_inicio < cursor_data_hora,
                    and_(FiscalEventModel.data_hora_inicio == cursor_data_hora, FiscalEventModel.id < cursor_id),
                )
            )
        stmt = stmt.order_by(FiscalEventModel.data_hora_inicio.desc(), FiscalEventModel.id.desc()).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def add(self, aggregate: FiscalEvent) -> None:
        tenant_id = get_current_tenant_id()
        model = FiscalEventModel(
            id=aggregate.id, tenant_id=tenant_id, documento_tipo=aggregate.documento_tipo.value,
            documento_id=aggregate.documento_id, tipo_evento=aggregate.tipo_evento.value,
            payload_arquivo_id=aggregate.payload_arquivo_id, protocolo_externo=aggregate.protocolo_externo,
            data_hora_inicio=aggregate.data_hora_inicio, data_hora_fim=aggregate.data_hora_fim,
            numero_tentativa=aggregate.numero_tentativa,
            resultado=aggregate.resultado.value if aggregate.resultado is not None else None,
            origem=aggregate.origem,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, attribute_names=["duracao_ms"])
        aggregate.duracao_ms = model.duracao_ms

    async def find(self, specification: Specification[FiscalEvent]) -> list[FiscalEvent]:
        raise NotImplementedError("Use list_page — filtros de FiscalEvent são resolvidos via SQL")
