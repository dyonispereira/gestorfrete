from __future__ import annotations

import uuid
from datetime import date, datetime

from core.exceptions.base import DomainError
from modules.drivers.domain.value_objects.cnh_category import CnhCategory
from modules.drivers.domain.value_objects.document_status import DocumentStatus
from modules.drivers.domain.value_objects.document_type import DocumentType
from shared_kernel.domain.base_entity import BaseEntity


class DriverDocument(BaseEntity[uuid.UUID]):
    """Não-Aggregate-Root — parte do agregado Motorista, lido/salvo pelo seu próprio Repository
    (D183, `DRIVER_IMPLEMENTATION.md`). A DDL física tem uma coluna `status` real (não apenas
    `data_validade`) — mas ela nunca é uma segunda fonte de verdade aqui: `status` é uma
    `@property` recalculada a partir de `data_validade` toda vez que é lida, e o Repository grava
    esse valor sempre fresco (`aggregate.status.value`) a cada `add()`, nunca confiando num valor
    de `status` vindo de fora."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        motorista_id: uuid.UUID,
        tipo_documento: DocumentType,
        numero: str,
        categoria_cnh: CnhCategory | None,
        data_validade: date | None,
        arquivo_id: uuid.UUID | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        if categoria_cnh is not None and tipo_documento != DocumentType.CNH:
            raise DomainError(
                "DRIVERS_CNH_CATEGORY_REQUIRES_CNH_TYPE", "Categoria só pode ser informada para documentos do tipo CNH."
            )
        super().__init__(id)
        self.motorista_id = motorista_id
        self.tipo_documento = tipo_documento
        self.numero = numero
        self.categoria_cnh = categoria_cnh
        self.data_validade = data_validade
        self.arquivo_id = arquivo_id
        self.created_at = created_at
        self.updated_at = updated_at

    @property
    def status(self) -> DocumentStatus:
        if self.data_validade is None:
            return DocumentStatus.VALIDO
        return DocumentStatus.VALIDO if self.data_validade >= date.today() else DocumentStatus.VENCIDO

    @classmethod
    def create(
        cls,
        *,
        motorista_id: uuid.UUID,
        tipo_documento: DocumentType,
        numero: str,
        categoria_cnh: CnhCategory | None,
        data_validade: date | None,
        arquivo_id: uuid.UUID | None,
        now: datetime,
    ) -> "DriverDocument":
        return cls(
            id=uuid.uuid4(),
            motorista_id=motorista_id,
            tipo_documento=tipo_documento,
            numero=numero,
            categoria_cnh=categoria_cnh,
            data_validade=data_validade,
            arquivo_id=arquivo_id,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        *,
        numero: str | None,
        categoria_cnh: CnhCategory | None,
        data_validade: date | None,
        arquivo_id: uuid.UUID | None,
        now: datetime,
    ) -> None:
        if numero is not None:
            self.numero = numero
        if categoria_cnh is not None:
            if self.tipo_documento != DocumentType.CNH:
                raise DomainError(
                    "DRIVERS_CNH_CATEGORY_REQUIRES_CNH_TYPE",
                    "Categoria só pode ser informada para documentos do tipo CNH.",
                )
            self.categoria_cnh = categoria_cnh
        if data_validade is not None:
            self.data_validade = data_validade
        if arquivo_id is not None:
            self.arquivo_id = arquivo_id
        self.updated_at = now
