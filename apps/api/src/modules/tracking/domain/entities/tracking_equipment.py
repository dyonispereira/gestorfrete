from __future__ import annotations

import uuid
from datetime import datetime

from modules.tracking.domain.value_objects.equipment_status import EquipmentStatus
from modules.tracking.domain.value_objects.equipment_type import EquipmentType
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class TrackingEquipment(BaseAggregateRoot[uuid.UUID]):
    """`equipamentos_rastreamento` — D128: um Veículo pode ter N equipamentos simultâneos, cada um
    com seu papel; no máximo um `PRINCIPAL` vigente (`data_fim_vigencia IS NULL`) por vez, garantido
    fisicamente por `uq_equipamentos_rastreamento_principal_vigente`."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        provedor_rastreamento_id: uuid.UUID,
        identificador_serial: str,
        tipo_equipamento: EquipmentType,
        veiculo_tracionador_id: uuid.UUID | None,
        data_inicio_vigencia: datetime | None,
        data_fim_vigencia: datetime | None,
        alterado_por: uuid.UUID | None,
        status: EquipmentStatus,
    ) -> None:
        super().__init__(id)
        self.provedor_rastreamento_id = provedor_rastreamento_id
        self.identificador_serial = identificador_serial
        self.tipo_equipamento = tipo_equipamento
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.data_inicio_vigencia = data_inicio_vigencia
        self.data_fim_vigencia = data_fim_vigencia
        self.alterado_por = alterado_por
        self.status = status

    @classmethod
    def create(
        cls,
        *,
        provedor_rastreamento_id: uuid.UUID,
        identificador_serial: str,
        tipo_equipamento: EquipmentType,
        veiculo_tracionador_id: uuid.UUID | None,
        now: datetime,
    ) -> "TrackingEquipment":
        return cls(
            id=uuid.uuid4(), provedor_rastreamento_id=provedor_rastreamento_id,
            identificador_serial=identificador_serial, tipo_equipamento=tipo_equipamento,
            veiculo_tracionador_id=veiculo_tracionador_id,
            data_inicio_vigencia=now if veiculo_tracionador_id is not None else None,
            data_fim_vigencia=None, alterado_por=None, status=EquipmentStatus.ATIVO,
        )

    def is_principal_vigente(self) -> bool:
        return self.tipo_equipamento == EquipmentType.PRINCIPAL and self.data_fim_vigencia is None

    def update(
        self,
        *,
        veiculo_tracionador_id: uuid.UUID | None,
        ends_at: datetime | None,
        status: EquipmentStatus | None,
        alterado_por: uuid.UUID | None,
        now: datetime,
    ) -> None:
        if veiculo_tracionador_id is not None:
            self.veiculo_tracionador_id = veiculo_tracionador_id
            if self.data_inicio_vigencia is None:
                self.data_inicio_vigencia = now
        if ends_at is not None:
            self.data_fim_vigencia = ends_at
        if status is not None:
            self.status = status
        if alterado_por is not None:
            self.alterado_por = alterado_por
