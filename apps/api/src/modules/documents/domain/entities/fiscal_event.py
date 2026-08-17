from __future__ import annotations

import uuid
from datetime import datetime

from modules.documents.domain.value_objects.fiscal_event_document_type import FiscalEventDocumentType
from modules.documents.domain.value_objects.fiscal_event_result import FiscalEventResult
from modules.documents.domain.value_objects.fiscal_event_type import FiscalEventType
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class FiscalEvent(BaseAggregateRoot[uuid.UUID]):
    """`eventos_fiscais` — log técnico bruto (D105), distinto dos `*StatusHistory` de negócio
    (D281). Somente leitura para usuários (D277) — nasce só como efeito colateral da integração.
    `duracao_ms` é `GENERATED ALWAYS AS (...) STORED` no Postgres — nunca calculado aqui, sempre
    lido de volta do banco (mesmo padrão de `Trip.margem_prevista`, D382)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        documento_tipo: FiscalEventDocumentType,
        documento_id: uuid.UUID,
        tipo_evento: FiscalEventType,
        payload_arquivo_id: uuid.UUID,
        protocolo_externo: str | None,
        data_hora_inicio: datetime,
        data_hora_fim: datetime | None,
        duracao_ms: int | None,
        numero_tentativa: int,
        resultado: FiscalEventResult | None,
        origem: str,
    ) -> None:
        super().__init__(id)
        self.documento_tipo = documento_tipo
        self.documento_id = documento_id
        self.tipo_evento = tipo_evento
        self.payload_arquivo_id = payload_arquivo_id
        self.protocolo_externo = protocolo_externo
        self.data_hora_inicio = data_hora_inicio
        self.data_hora_fim = data_hora_fim
        self.duracao_ms = duracao_ms
        self.numero_tentativa = numero_tentativa
        self.resultado = resultado
        self.origem = origem

    @classmethod
    def create(
        cls,
        *,
        documento_tipo: FiscalEventDocumentType,
        documento_id: uuid.UUID,
        tipo_evento: FiscalEventType,
        payload_arquivo_id: uuid.UUID,
        protocolo_externo: str | None,
        numero_tentativa: int,
        resultado: FiscalEventResult | None,
        origem: str,
        data_hora_inicio: datetime,
        data_hora_fim: datetime | None,
    ) -> "FiscalEvent":
        return cls(
            id=uuid.uuid4(), documento_tipo=documento_tipo, documento_id=documento_id,
            tipo_evento=tipo_evento, payload_arquivo_id=payload_arquivo_id,
            protocolo_externo=protocolo_externo, data_hora_inicio=data_hora_inicio,
            data_hora_fim=data_hora_fim, duracao_ms=None, numero_tentativa=numero_tentativa,
            resultado=resultado, origem=origem,
        )
