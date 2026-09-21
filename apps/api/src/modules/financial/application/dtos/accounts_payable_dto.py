from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from modules.financial.domain.entities.accounts_payable import AccountsPayable


@dataclass(frozen=True)
class AccountsPayableDTO:
    id: uuid.UUID
    fornecedor_id: uuid.UUID
    centro_custo_id: uuid.UUID
    origem: str
    viagem_id: uuid.UUID | None
    ordem_servico_id: uuid.UUID | None
    veiculo_tracionador_id: uuid.UUID | None
    motorista_id: uuid.UUID | None
    valor: Decimal
    data_vencimento: date
    competencia: date
    plano_contas_id: uuid.UUID
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(entity: AccountsPayable) -> "AccountsPayableDTO":
        return AccountsPayableDTO(
            id=entity.id, fornecedor_id=entity.fornecedor_id, centro_custo_id=entity.centro_custo_id,
            origem=entity.origem.value, viagem_id=entity.viagem_id, ordem_servico_id=entity.ordem_servico_id,
            veiculo_tracionador_id=entity.veiculo_tracionador_id, motorista_id=entity.motorista_id,
            valor=entity.valor, data_vencimento=entity.data_vencimento, competencia=entity.competencia,
            plano_contas_id=entity.plano_contas_id, status=entity.status.value,
            created_at=entity.audit.created_at, created_by=entity.audit.created_by,
            updated_at=entity.audit.updated_at, updated_by=entity.audit.updated_by,
        )
