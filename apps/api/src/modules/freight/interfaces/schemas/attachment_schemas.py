from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from shared.collaboration.domain.entities.attachment import Attachment
from shared_kernel.domain.audit_metadata import AuditMetadata


class CreateAttachmentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    attachment_type: str
    file_id: uuid.UUID
    description: str | None = None


class AttachmentResponse(BaseModel):
    id: uuid.UUID
    attachment_type: str
    file_id: uuid.UUID
    description: str | None
    audit: AuditMetadata

    @staticmethod
    def from_entity(attachment: Attachment) -> "AttachmentResponse":
        return AttachmentResponse(
            id=attachment.id, attachment_type=attachment.tipo_anexo, file_id=attachment.arquivo_id,
            description=attachment.descricao,
            # D415-adjacent: `anexos` não tem `atualizado_em`/`atualizado_por` — imutável, então
            # `updated_at`/`updated_by` sempre espelham `created_at`/`created_by` (mesma disciplina
            # de D400/D381).
            audit=AuditMetadata(
                created_at=attachment.criado_em, created_by=attachment.criado_por,
                updated_at=attachment.criado_em, updated_by=attachment.criado_por,
            ),
        )
