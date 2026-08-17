from __future__ import annotations

from dataclasses import dataclass

from modules.identity_access.application.dtos.user_dto import UserDTO
from modules.tenancy.application.dtos.tenant_dto import TenantDTO


@dataclass(frozen=True)
class TokenPairDTO:
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True)
class LoginResultDTO(TokenPairDTO):
    user: UserDTO


@dataclass(frozen=True)
class SessionDTO:
    id: str
    started_at: str
    expires_at: str
    status: str


@dataclass(frozen=True)
class MeResultDTO:
    user: UserDTO
    tenant: TenantDTO
    session: SessionDTO
    role_names: list[str]
