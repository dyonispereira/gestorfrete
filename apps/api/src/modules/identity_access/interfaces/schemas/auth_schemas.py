from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from modules.identity_access.application.dtos.auth_dto import LoginResultDTO, MeResultDTO, TokenPairDTO
from modules.identity_access.application.dtos.user_dto import UserDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    refresh_token: str


class UserSummaryResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    nome: str
    email: str
    status: str
    driver_id: uuid.UUID | None
    employee_id: uuid.UUID | None
    roles: list[uuid.UUID]
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: UserDTO) -> "UserSummaryResponse":
        return UserSummaryResponse(
            id=dto.id,
            codigo=dto.codigo,
            nome=dto.nome,
            email=dto.email,
            status=dto.status,
            driver_id=dto.driver_id,
            employee_id=dto.employee_id,
            roles=sorted(dto.role_ids, key=str),
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int

    @staticmethod
    def from_dto(dto: TokenPairDTO) -> "TokenPairResponse":
        return TokenPairResponse(
            access_token=dto.access_token, refresh_token=dto.refresh_token, expires_in=dto.expires_in
        )


class LoginResponse(TokenPairResponse):
    user: UserSummaryResponse

    @staticmethod
    def from_login_dto(dto: LoginResultDTO) -> "LoginResponse":
        return LoginResponse(
            access_token=dto.access_token,
            refresh_token=dto.refresh_token,
            expires_in=dto.expires_in,
            user=UserSummaryResponse.from_dto(dto.user),
        )


class TenantContextResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    razao_social: str
    status: str


class SessionResponse(BaseModel):
    id: uuid.UUID
    started_at: datetime
    expires_at: datetime
    status: str


class MeResponse(BaseModel):
    user: UserSummaryResponse
    tenant: TenantContextResponse
    session: SessionResponse
    roles: list[str]

    @staticmethod
    def from_dto(dto: MeResultDTO) -> "MeResponse":
        return MeResponse(
            user=UserSummaryResponse.from_dto(dto.user),
            tenant=TenantContextResponse(
                id=dto.tenant.id, codigo=dto.tenant.codigo, razao_social=dto.tenant.razao_social, status=dto.tenant.status
            ),
            session=SessionResponse(
                id=uuid.UUID(dto.session.id),
                started_at=datetime.fromisoformat(dto.session.started_at),
                expires_at=datetime.fromisoformat(dto.session.expires_at),
                status=dto.session.status,
            ),
            roles=dto.role_names,
        )
