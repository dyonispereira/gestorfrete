from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.documents.domain.entities.cte import Cte


@dataclass(frozen=True)
class CteDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    numero: str
    serie: str
    chave_acesso: str | None
    valor_servico: Decimal
    status: str
    xml_arquivo_id: uuid.UUID | None
    protocolo_sefaz: str | None
    data_hora_autorizacao: datetime | None
    criado_em: datetime
    atualizado_em: datetime

    @staticmethod
    def from_entity(entity: Cte) -> "CteDTO":
        return CteDTO(
            id=entity.id, viagem_id=entity.viagem_id, numero=entity.numero, serie=entity.serie,
            chave_acesso=entity.chave_acesso, valor_servico=entity.valor_servico, status=entity.status.value,
            xml_arquivo_id=entity.xml_arquivo_id, protocolo_sefaz=entity.protocolo_sefaz,
            data_hora_autorizacao=entity.data_hora_autorizacao, criado_em=entity.criado_em,
            atualizado_em=entity.atualizado_em,
        )
