from __future__ import annotations

import uuid
from datetime import datetime

from modules.mobile.domain.value_objects.auth_method import AuthMethod
from modules.mobile.domain.value_objects.mobile_session_end_reason import MobileSessionEndReason
from modules.mobile.domain.value_objects.mobile_session_status import MobileSessionStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class MobileSession(BaseAggregateRoot[uuid.UUID]):
    """`sessoes_mobile` — D140: nunca representa identidade (só `motorista_id` referencia quem é a
    pessoa), nunca cacheia RBAC (D060/D296). D407 — `id` é sempre igual ao `Session.id`
    (`sessoes_acesso`, `identity_access`) criado na mesma operação de login; nunca gerado
    independentemente."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        motorista_id: uuid.UUID,
        veiculo_tracionador_id: uuid.UUID,
        dispositivo_mobile_id: uuid.UUID,
        metodo_autenticacao: AuthMethod,
        token_acesso_hash: str,
        data_hora_inicio: datetime,
        data_hora_expiracao_prevista: datetime,
        data_hora_encerramento: datetime | None,
        motivo_encerramento: MobileSessionEndReason | None,
        revogado_por: uuid.UUID | None,
        status: MobileSessionStatus,
    ) -> None:
        super().__init__(id)
        self.motorista_id = motorista_id
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.dispositivo_mobile_id = dispositivo_mobile_id
        self.metodo_autenticacao = metodo_autenticacao
        self.token_acesso_hash = token_acesso_hash
        self.data_hora_inicio = data_hora_inicio
        self.data_hora_expiracao_prevista = data_hora_expiracao_prevista
        self.data_hora_encerramento = data_hora_encerramento
        self.motivo_encerramento = motivo_encerramento
        self.revogado_por = revogado_por
        self.status = status

    @classmethod
    def start(
        cls,
        *,
        id: uuid.UUID,
        motorista_id: uuid.UUID,
        veiculo_tracionador_id: uuid.UUID,
        dispositivo_mobile_id: uuid.UUID,
        metodo_autenticacao: AuthMethod,
        token_acesso_hash: str,
        started_at: datetime,
        expires_at: datetime,
    ) -> "MobileSession":
        return cls(
            id=id, motorista_id=motorista_id, veiculo_tracionador_id=veiculo_tracionador_id,
            dispositivo_mobile_id=dispositivo_mobile_id, metodo_autenticacao=metodo_autenticacao,
            token_acesso_hash=token_acesso_hash, data_hora_inicio=started_at,
            data_hora_expiracao_prevista=expires_at, data_hora_encerramento=None,
            motivo_encerramento=None, revogado_por=None, status=MobileSessionStatus.ATIVA,
        )

    def end(
        self, *, reason: MobileSessionEndReason, now: datetime, revoked_by: uuid.UUID | None = None
    ) -> None:
        self.status = MobileSessionStatus.ENCERRADA
        self.motivo_encerramento = reason
        self.data_hora_encerramento = now
        self.revogado_por = revoked_by
