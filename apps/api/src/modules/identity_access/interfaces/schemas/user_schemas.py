from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from modules.identity_access.interfaces.schemas.auth_schemas import UserSummaryResponse

UserResponse = UserSummaryResponse
"""Mesmo schema de `GET /auth/me`'s `user` — `003-users.md` e `001-authentication.md` descrevem o
mesmo recurso `User` (`components/schemas.md#User`), nunca dois formatos divergentes."""


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str
    email: EmailStr
    password: str = Field(min_length=8)
    driver_id: uuid.UUID | None = None
    employee_id: uuid.UUID | None = None
    role_ids: list[uuid.UUID] = Field(default_factory=list)


class UpdateUserRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    email: EmailStr | None = None
    role_ids: list[uuid.UUID] | None = None
