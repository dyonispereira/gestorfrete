from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.documents.application.dtos.referenced_nfe_dto import ReferencedNfeDTO


class ReferencedNfeResponse(BaseModel):
    id: uuid.UUID
    access_key: str
    xml_file_id: uuid.UUID | None

    @staticmethod
    def from_dto(dto: ReferencedNfeDTO) -> "ReferencedNfeResponse":
        return ReferencedNfeResponse(id=dto.id, access_key=dto.chave_acesso, xml_file_id=dto.xml_arquivo_id)


class CreateReferencedNfeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_key: str
