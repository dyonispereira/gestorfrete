from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.mobile.domain.entities.mobile_session import MobileSession


@dataclass(frozen=True)
class MobileSessionDTO:
    id: uuid.UUID
    motorista_id: uuid.UUID
    veiculo_tracionador_id: uuid.UUID
    dispositivo_mobile_id: uuid.UUID
    metodo_autenticacao: str
    data_hora_inicio: datetime
    data_hora_expiracao_prevista: datetime
    data_hora_encerramento: datetime | None
    motivo_encerramento: str | None
    status: str

    @staticmethod
    def from_entity(entity: MobileSession) -> "MobileSessionDTO":
        return MobileSessionDTO(
            id=entity.id, motorista_id=entity.motorista_id, veiculo_tracionador_id=entity.veiculo_tracionador_id,
            dispositivo_mobile_id=entity.dispositivo_mobile_id, metodo_autenticacao=entity.metodo_autenticacao.value,
            data_hora_inicio=entity.data_hora_inicio, data_hora_expiracao_prevista=entity.data_hora_expiracao_prevista,
            data_hora_encerramento=entity.data_hora_encerramento,
            motivo_encerramento=entity.motivo_encerramento.value if entity.motivo_encerramento else None,
            status=entity.status.value,
        )
