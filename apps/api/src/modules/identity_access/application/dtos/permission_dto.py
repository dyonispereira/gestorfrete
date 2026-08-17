from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.identity_access.domain.entities.permission import Permission


@dataclass(frozen=True)
class PermissionDTO:
    id: uuid.UUID
    code: str
    name: str
    module: str

    @staticmethod
    def from_entity(permission: Permission) -> "PermissionDTO":
        return PermissionDTO(id=permission.id, code=permission.code, name=permission.name, module=permission.module)
