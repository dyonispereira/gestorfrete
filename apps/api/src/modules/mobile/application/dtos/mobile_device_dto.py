from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.mobile.domain.entities.mobile_device import MobileDevice


@dataclass(frozen=True)
class MobileDeviceDTO:
    id: uuid.UUID
    identificador_dispositivo: str
    sistema_operacional: str
    versao_so: str | None
    versao_app: str
    status: str
    ultimo_acesso_em: datetime | None

    @staticmethod
    def from_entity(entity: MobileDevice) -> "MobileDeviceDTO":
        return MobileDeviceDTO(
            id=entity.id, identificador_dispositivo=entity.identificador_dispositivo,
            sistema_operacional=entity.sistema_operacional.value, versao_so=entity.versao_so,
            versao_app=entity.versao_app, status=entity.status.value, ultimo_acesso_em=entity.ultimo_acesso_em,
        )
