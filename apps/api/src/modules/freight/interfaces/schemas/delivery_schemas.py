from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.freight.application.dtos.delivery_dto import DeliveryDTO
from modules.freight.application.dtos.proof_of_delivery_dto import ProofOfDeliveryDTO


class DeliveryWindowPayload(BaseModel):
    starts_at: datetime
    ends_at: datetime


class DeliveryResponse(BaseModel):
    """`trip-schemas.md#Delivery` inclui `audit`, mas `entregas` (`relational/003-operacao.md`) não
    tem nenhuma coluna de timestamp/ator — lacuna na própria documentação congelada (D381), mesma
    família do `ocorrencias.location` já registrado em `017-trip-occurrences.md`. `audit` omitido
    aqui em vez de inventado."""

    id: uuid.UUID
    order: int
    recipient: str
    delivery_address: dict[str, Any]
    status: str
    completed_at: datetime | None
    rejection_reason: str | None
    window: DeliveryWindowPayload | None

    @staticmethod
    def from_dto(dto: DeliveryDTO) -> "DeliveryResponse":
        window = None
        if dto.window_hora_inicio is not None and dto.window_hora_fim is not None:
            window = DeliveryWindowPayload(starts_at=dto.window_hora_inicio, ends_at=dto.window_hora_fim)
        return DeliveryResponse(
            id=dto.id, order=dto.ordem, recipient=dto.destinatario, delivery_address=dto.endereco_entrega,
            status=dto.status, completed_at=dto.data_hora_conclusao, rejection_reason=dto.motivo_recusa, window=window,
        )


class CreateDeliveryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order: int
    recipient: str
    delivery_address: dict[str, Any]
    window: DeliveryWindowPayload | None = None


class UpdateDeliveryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipient: str | None = None
    delivery_address: dict[str, Any] | None = None
    status: str | None = None
    rejection_reason: str | None = None


class ProofOfDeliveryResponse(BaseModel):
    id: uuid.UUID
    status: str
    registered_at: datetime | None
    signature_file_id: uuid.UUID | None

    @staticmethod
    def from_dto(dto: ProofOfDeliveryDTO) -> "ProofOfDeliveryResponse":
        return ProofOfDeliveryResponse(
            id=dto.id, status=dto.status, registered_at=dto.data_hora_registro, signature_file_id=dto.assinatura_arquivo_id
        )


class RegisterProofOfDeliveryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    signature_file_id: uuid.UUID | None = None
