from __future__ import annotations

import uuid
from datetime import datetime

from modules.mobile.domain.value_objects.device_os import DeviceOS
from modules.mobile.domain.value_objects.device_status import DeviceStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class MobileDevice(BaseAggregateRoot[uuid.UUID]):
    """`dispositivos_mobile` — persistente entre sessões, ao contrário de `MobileSession`.
    `identificador_dispositivo` nunca muda depois do primeiro registro (D084)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        motorista_id: uuid.UUID,
        identificador_dispositivo: str,
        sistema_operacional: DeviceOS,
        versao_so: str | None,
        versao_app: str,
        token_push: str | None,
        status: DeviceStatus,
        ultimo_acesso_em: datetime | None,
    ) -> None:
        super().__init__(id)
        self.motorista_id = motorista_id
        self.identificador_dispositivo = identificador_dispositivo
        self.sistema_operacional = sistema_operacional
        self.versao_so = versao_so
        self.versao_app = versao_app
        self.token_push = token_push
        self.status = status
        self.ultimo_acesso_em = ultimo_acesso_em

    @classmethod
    def register(
        cls,
        *,
        motorista_id: uuid.UUID,
        identificador_dispositivo: str,
        sistema_operacional: DeviceOS,
        versao_so: str | None,
        versao_app: str,
        token_push: str | None,
        now: datetime,
    ) -> "MobileDevice":
        return cls(
            id=uuid.uuid4(), motorista_id=motorista_id, identificador_dispositivo=identificador_dispositivo,
            sistema_operacional=sistema_operacional, versao_so=versao_so, versao_app=versao_app,
            token_push=token_push, status=DeviceStatus.ATIVO, ultimo_acesso_em=now,
        )

    def touch_access(self, now: datetime) -> None:
        """D081 — projeção da última `MobileSession` aberta neste dispositivo."""

        self.ultimo_acesso_em = now

    def update_self_service(
        self, *, os_version: str | None, app_version: str | None, push_token: str | None,
        status: DeviceStatus | None,
    ) -> None:
        """D302 — atualizar `token_push` nunca dispara efeito de domínio, só troca o valor guardado."""

        if os_version is not None:
            self.versao_so = os_version
        if app_version is not None:
            self.versao_app = app_version
        if push_token is not None:
            self.token_push = push_token
        if status is not None:
            self.status = status
