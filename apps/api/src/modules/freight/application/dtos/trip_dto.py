from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from modules.freight.domain.entities.trip import Trip


@dataclass(frozen=True)
class TripDTO:
    id: uuid.UUID
    codigo: str
    data_programada: date | None
    janela_programada: datetime | None
    cliente_id: uuid.UUID
    motorista_id: uuid.UUID | None
    veiculo_tracionador_id: uuid.UUID | None
    status_operacional: str
    status_fiscal: str
    status_financeiro: str
    encerrada: bool
    nome_motorista_snapshot: str | None
    placa_veiculo_snapshot: str | None
    cliente_snapshot: dict[str, Any] | None
    receita_prevista_snapshot: Decimal | None
    tabela_preco_aplicada_snapshot_id: uuid.UUID | None
    custo_previsto: Decimal | None
    custo_realizado: Decimal | None
    receita_realizada: Decimal | None
    margem_prevista: Decimal | None
    margem_realizada: Decimal | None
    desvio_financeiro: Decimal | None
    km_rodado: Decimal | None
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_entity(trip: Trip) -> "TripDTO":
        return TripDTO(
            id=trip.id,
            codigo=trip.codigo,
            data_programada=trip.data_programada,
            janela_programada=trip.janela_programada,
            cliente_id=trip.cliente_id,
            motorista_id=trip.motorista_id,
            veiculo_tracionador_id=trip.veiculo_tracionador_id,
            status_operacional=trip.status_operacional.value,
            status_fiscal=trip.status_fiscal.value,
            status_financeiro=trip.status_financeiro.value,
            encerrada=trip.encerrada,
            nome_motorista_snapshot=trip.nome_motorista_snapshot,
            placa_veiculo_snapshot=trip.placa_veiculo_snapshot,
            cliente_snapshot=trip.cliente_snapshot,
            receita_prevista_snapshot=trip.receita_prevista_snapshot,
            tabela_preco_aplicada_snapshot_id=trip.tabela_preco_aplicada_snapshot_id,
            custo_previsto=trip.custo_previsto,
            custo_realizado=trip.custo_realizado,
            receita_realizada=trip.receita_realizada,
            margem_prevista=trip.margem_prevista,
            margem_realizada=trip.margem_realizada,
            desvio_financeiro=trip.desvio_financeiro,
            km_rodado=trip.km_rodado,
            created_at=trip.audit.created_at,
            created_by=trip.audit.created_by,
            updated_at=trip.audit.updated_at,
            updated_by=trip.audit.updated_by,
        )
