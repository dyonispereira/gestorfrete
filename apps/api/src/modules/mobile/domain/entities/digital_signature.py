from __future__ import annotations

import uuid
from datetime import datetime

from modules.mobile.domain.value_objects.signatory_role import SignatoryRole
from modules.mobile.domain.value_objects.signature_document_type import SignatureDocumentType
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class DigitalSignature(BaseAggregateRoot[uuid.UUID]):
    """`assinaturas_digitais` — imutável (D037/D123): corrigir uma assinatura errada é recapturar
    (novo Canhoto), nunca editar a existente."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        documento_tipo: SignatureDocumentType,
        documento_id: uuid.UUID,
        papel_signatario: SignatoryRole,
        nome_signatario_informado: str | None,
        arquivo_id: uuid.UUID,
        data_hora_captura: datetime,
        data_hora_recebimento: datetime,
    ) -> None:
        super().__init__(id)
        self.documento_tipo = documento_tipo
        self.documento_id = documento_id
        self.papel_signatario = papel_signatario
        self.nome_signatario_informado = nome_signatario_informado
        self.arquivo_id = arquivo_id
        self.data_hora_captura = data_hora_captura
        self.data_hora_recebimento = data_hora_recebimento

    @classmethod
    def capture(
        cls,
        *,
        documento_tipo: SignatureDocumentType,
        documento_id: uuid.UUID,
        papel_signatario: SignatoryRole,
        nome_signatario_informado: str | None,
        arquivo_id: uuid.UUID,
        captured_at: datetime,
        received_at: datetime,
    ) -> "DigitalSignature":
        return cls(
            id=uuid.uuid4(), documento_tipo=documento_tipo, documento_id=documento_id,
            papel_signatario=papel_signatario, nome_signatario_informado=nome_signatario_informado,
            arquivo_id=arquivo_id, data_hora_captura=captured_at, data_hora_recebimento=received_at,
        )
