from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import DomainError
from modules.freight.domain.value_objects.allocation_status import AllocationStatus
from shared_kernel.domain.base_entity import BaseEntity


class TripAllocation(BaseEntity[uuid.UUID]):
    """`alocacoes_recurso_viagem` — pacote atômico (D188), nunca Motorista/Veículo/Implemento como
    recursos independentes. `viagens.motorista_id`/`veiculo_tracionador_id` são mantidos em
    sincronia pelo Handler via `Trip.set_current_allocation(...)`, nunca lidos de volta daqui por
    JOIN (`TRIP_IMPLEMENTATION.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        viagem_id: uuid.UUID,
        motorista_id: uuid.UUID,
        veiculo_tracionador_id: uuid.UUID,
        implemento_id: uuid.UUID | None,
        status: AllocationStatus,
        motivo_troca: str | None,
        criado_em: datetime,
        criado_por: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.motorista_id = motorista_id
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.implemento_id = implemento_id
        self.status = status
        self.motivo_troca = motivo_troca
        self.criado_em = criado_em
        self.criado_por = criado_por

    @classmethod
    def create(
        cls,
        *,
        viagem_id: uuid.UUID,
        motorista_id: uuid.UUID,
        veiculo_tracionador_id: uuid.UUID,
        implemento_id: uuid.UUID | None,
        motivo_troca: str | None,
        now: datetime,
        created_by: uuid.UUID | None,
    ) -> "TripAllocation":
        return cls(
            id=uuid.uuid4(),
            viagem_id=viagem_id,
            motorista_id=motorista_id,
            veiculo_tracionador_id=veiculo_tracionador_id,
            implemento_id=implemento_id,
            status=AllocationStatus.VIGENTE,
            motivo_troca=motivo_troca,
            criado_em=now,
            criado_por=created_by,
        )

    def supersede(self) -> None:
        """Nunca edita a linha histórica "por cima" do valor anterior (D017/D018) — o Repository
        insere uma nova linha `VIGENTE`; esta chamada só marca a linha atual como substituída."""

        if self.status != AllocationStatus.VIGENTE:
            raise DomainError("FREIGHT_TRIP_ALLOCATION_ALREADY_SUPERSEDED", "Alocação já não está vigente.")
        self.status = AllocationStatus.SUBSTITUIDA

    def end(self) -> None:
        """V1 Operational Hardening, Parte 1 — a Viagem dona terminou (`Finalizada`/`Cancelada`,
        por qualquer um dos três comandos que produzem esses estados). Distinto de `supersede()`:
        aqui não existe uma nova Alocação assumindo o lugar desta — o Veículo simplesmente para de
        estar comprometido por esta Viagem. `exists_vigente_for_vehicle_excluding_trip` só enxerga
        `VIGENTE`, então esta transição é o que libera o Veículo para uma nova Viagem."""

        if self.status != AllocationStatus.VIGENTE:
            raise DomainError("FREIGHT_TRIP_ALLOCATION_ALREADY_SUPERSEDED", "Alocação já não está vigente.")
        self.status = AllocationStatus.ENCERRADA
