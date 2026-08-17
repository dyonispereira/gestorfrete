from __future__ import annotations

import uuid
from datetime import date

from modules.fleet.domain.value_objects.vehicle_document_status import VehicleDocumentStatus
from shared_kernel.domain.base_entity import BaseEntity


class VehicleDocument(BaseEntity[uuid.UUID]):
    """Não-Aggregate-Root — parte do agregado Vehicle. Sem colunas de timestamp — a DDL
    (`documentos_veiculo`) não as tem (`VEHICLE_IMPLEMENTATION.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        veiculo_tracionador_id: uuid.UUID,
        tipo: str,
        numero: str,
        data_validade: date,
        arquivo_id: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.tipo = tipo
        self.numero = numero
        self.data_validade = data_validade
        self.arquivo_id = arquivo_id

    @property
    def status(self) -> VehicleDocumentStatus:
        return VehicleDocumentStatus.VALIDO if self.data_validade >= date.today() else VehicleDocumentStatus.VENCIDO

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        tipo: str,
        numero: str,
        data_validade: date,
        arquivo_id: uuid.UUID | None,
    ) -> "VehicleDocument":
        return cls(
            id=uuid.uuid4(),
            veiculo_tracionador_id=veiculo_tracionador_id,
            tipo=tipo,
            numero=numero,
            data_validade=data_validade,
            arquivo_id=arquivo_id,
        )

    def update(self, *, numero: str | None, data_validade: date | None, arquivo_id: uuid.UUID | None) -> None:
        if numero is not None:
            self.numero = numero
        if data_validade is not None:
            self.data_validade = data_validade
        if arquivo_id is not None:
            self.arquivo_id = arquivo_id
