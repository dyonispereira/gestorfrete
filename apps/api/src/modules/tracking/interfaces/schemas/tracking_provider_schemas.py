from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.tracking.application.dtos.tracking_provider_dto import TrackingProviderDTO


class TrackingProviderResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: str

    @staticmethod
    def from_dto(dto: TrackingProviderDTO) -> "TrackingProviderResponse":
        return TrackingProviderResponse(id=dto.id, name=dto.nome, status=dto.status)


class CreateTrackingProviderRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str


class UpdateTrackingProviderRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    status: str | None = None
