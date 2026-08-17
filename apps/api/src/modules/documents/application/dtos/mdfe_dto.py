from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.documents.domain.entities.mdfe import Mdfe


@dataclass(frozen=True)
class MdfeDTO:
    id: uuid.UUID
    viagem_id: uuid.UUID
    numero: str
    serie: str
    chave_acesso: str | None
    status: str
    xml_arquivo_id: uuid.UUID | None
    protocolo_sefaz: str | None
    data_hora_encerramento: datetime | None
    cte_ids: list[uuid.UUID]

    @staticmethod
    def from_entity(entity: Mdfe, *, cte_ids: list[uuid.UUID]) -> "MdfeDTO":
        return MdfeDTO(
            id=entity.id, viagem_id=entity.viagem_id, numero=entity.numero, serie=entity.serie,
            chave_acesso=entity.chave_acesso, status=entity.status.value, xml_arquivo_id=entity.xml_arquivo_id,
            protocolo_sefaz=entity.protocolo_sefaz, data_hora_encerramento=entity.data_hora_encerramento,
            cte_ids=cte_ids,
        )
