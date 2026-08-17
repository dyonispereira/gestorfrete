from __future__ import annotations

import uuid
from datetime import datetime

from modules.freight.domain.value_objects.proof_of_delivery_status import ProofOfDeliveryStatus
from shared_kernel.domain.base_entity import BaseEntity


class ProofOfDelivery(BaseEntity[uuid.UUID]):
    """Canhoto — `canhotos`, 1:1 com Entrega (`uq_canhotos_entrega_id`, D373). Fotos adicionais
    usam o sistema compartilhado de Anexos (`entidade_tipo='CANHOTO'`), nunca binário aqui."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        entrega_id: uuid.UUID,
        status: ProofOfDeliveryStatus,
        data_hora_registro: datetime | None,
        assinatura_arquivo_id: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.entrega_id = entrega_id
        self.status = status
        self.data_hora_registro = data_hora_registro
        self.assinatura_arquivo_id = assinatura_arquivo_id

    @classmethod
    def create(
        cls, *, entrega_id: uuid.UUID, signature_file_id: uuid.UUID | None, now: datetime
    ) -> "ProofOfDelivery":
        return cls(
            id=uuid.uuid4(),
            entrega_id=entrega_id,
            status=ProofOfDeliveryStatus.REGISTRADO,
            data_hora_registro=now,
            assinatura_arquivo_id=signature_file_id,
        )
