from __future__ import annotations

import uuid

from pydantic import BaseModel

from modules.identity_access.application.dtos.permission_dto import PermissionDTO


class PermissionResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    module: str

    @staticmethod
    def from_dto(dto: PermissionDTO) -> "PermissionResponse":
        return PermissionResponse(id=dto.id, code=dto.code, name=dto.name, module=dto.module)
