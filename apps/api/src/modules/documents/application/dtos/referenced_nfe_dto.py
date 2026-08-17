from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.documents.domain.entities.referenced_nfe import ReferencedNfe


@dataclass(frozen=True)
class ReferencedNfeDTO:
    id: uuid.UUID
    cte_id: uuid.UUID
    chave_acesso: str
    xml_arquivo_id: uuid.UUID | None

    @staticmethod
    def from_entity(entity: ReferencedNfe) -> "ReferencedNfeDTO":
        return ReferencedNfeDTO(
            id=entity.id, cte_id=entity.cte_id, chave_acesso=entity.chave_acesso,
            xml_arquivo_id=entity.xml_arquivo_id,
        )
