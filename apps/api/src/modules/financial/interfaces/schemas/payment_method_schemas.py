from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.financial.application.dtos.payment_method_dto import PaymentMethodDTO


class PaymentMethodResponse(BaseModel):
    id: uuid.UUID
    nome: str
    status: str

    @staticmethod
    def from_dto(dto: PaymentMethodDTO) -> "PaymentMethodResponse":
        return PaymentMethodResponse(id=dto.id, nome=dto.nome, status=dto.status)


class CreatePaymentMethodRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str


class UpdatePaymentMethodRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    status: str | None = None
