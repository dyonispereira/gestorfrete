from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.mobile.application.dtos.mobile_device_dto import MobileDeviceDTO


class MobileDeviceResponse(BaseModel):
    id: uuid.UUID
    device_identifier: str
    os: str
    os_version: str | None
    app_version: str
    status: str
    last_access_at: datetime | None

    @staticmethod
    def from_dto(dto: MobileDeviceDTO) -> "MobileDeviceResponse":
        return MobileDeviceResponse(
            id=dto.id, device_identifier=dto.identificador_dispositivo, os=dto.sistema_operacional,
            os_version=dto.versao_so, app_version=dto.versao_app, status=dto.status,
            last_access_at=dto.ultimo_acesso_em,
        )


class UpdateMobileDeviceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    os_version: str | None = None
    app_version: str | None = None
    push_token: str | None = None
    status: str | None = None
