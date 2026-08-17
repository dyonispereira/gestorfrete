from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.reporting.application.dtos.saved_filter_dto import SavedFilterDTO


class CreateSavedFilterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    criteria: dict[str, Any]


class UpdateSavedFilterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    criteria: dict[str, Any] | None = None
    status: str | None = None


class SavedFilterResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    criteria: dict[str, Any]
    status: str

    @staticmethod
    def from_dto(dto: SavedFilterDTO) -> "SavedFilterResponse":
        return SavedFilterResponse(id=dto.id, user_id=dto.user_id, name=dto.name, criteria=dto.criteria, status=dto.status)
