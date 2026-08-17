from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.drivers.interfaces.schemas.driver_schemas import DriverResponse
from modules.identity_access.application.dtos.auth_dto import TokenPairDTO
from modules.mobile.application.dtos.mobile_login_result_dto import MobileLoginResultDTO
from modules.mobile.application.dtos.mobile_session_dto import MobileSessionDTO
from modules.mobile.application.queries.get_current_session import GetCurrentSessionResult


class MobileDeviceLoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    device_identifier: str
    os: str
    os_version: str | None = None
    app_version: str
    push_token: str | None = None


class MobileLoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cpf: str
    vehicle_plate: str | None = None
    auth_method: str
    credential: str
    device: MobileDeviceLoginRequest


class MobileRefreshRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    refresh_token: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int

    @staticmethod
    def from_dto(dto: TokenPairDTO) -> "TokenPairResponse":
        return TokenPairResponse(
            access_token=dto.access_token, refresh_token=dto.refresh_token, expires_in=dto.expires_in
        )


class MobileSessionResponse(BaseModel):
    id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    device_id: uuid.UUID
    auth_method: str
    started_at: datetime
    expires_at: datetime
    ended_at: datetime | None
    end_reason: str | None
    status: str

    @staticmethod
    def from_dto(dto: MobileSessionDTO) -> "MobileSessionResponse":
        return MobileSessionResponse(
            id=dto.id, driver_id=dto.motorista_id, vehicle_id=dto.veiculo_tracionador_id,
            device_id=dto.dispositivo_mobile_id, auth_method=dto.metodo_autenticacao,
            started_at=dto.data_hora_inicio, expires_at=dto.data_hora_expiracao_prevista,
            ended_at=dto.data_hora_encerramento, end_reason=dto.motivo_encerramento, status=dto.status,
        )


class MobileLoginResponse(TokenPairResponse):
    session: MobileSessionResponse
    driver: DriverResponse

    @staticmethod
    def from_login_dto(dto: MobileLoginResultDTO) -> "MobileLoginResponse":
        return MobileLoginResponse(
            access_token=dto.access_token, refresh_token=dto.refresh_token, expires_in=dto.expires_in,
            session=MobileSessionResponse.from_dto(dto.session), driver=DriverResponse.from_dto(dto.driver),
        )


class MobileMeResponse(BaseModel):
    session: MobileSessionResponse
    driver: DriverResponse

    @staticmethod
    def from_result(result: GetCurrentSessionResult) -> "MobileMeResponse":
        return MobileMeResponse(
            session=MobileSessionResponse.from_dto(result.session), driver=DriverResponse.from_dto(result.driver)
        )
