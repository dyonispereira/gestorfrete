from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.ai.application.dtos.ai_model_dto import AIModelDTO


class CreateAIModelRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    type: str
    version: str
    logical_provider: str
    capability: str
    max_context: int | None = None


class UpdateAIModelRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    capability: str | None = None
    max_context: int | None = None
    status: str | None = None


class AIModelResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    version: str
    logical_provider: str
    capability: str
    max_context: int | None
    status: str

    @staticmethod
    def from_dto(dto: AIModelDTO) -> "AIModelResponse":
        return AIModelResponse(
            id=dto.id, name=dto.name, type=dto.type, version=dto.version,
            logical_provider=dto.logical_provider, capability=dto.capability,
            max_context=dto.max_context, status=dto.status,
        )
