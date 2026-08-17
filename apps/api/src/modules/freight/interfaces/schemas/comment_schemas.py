from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from shared.collaboration.domain.entities.comment import Comment
from shared_kernel.domain.audit_metadata import AuditMetadata


class CreateCommentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str
    visible_to_client: bool = False


class UpdateCommentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str | None = None
    visible_to_client: bool | None = None


class CommentResponse(BaseModel):
    id: uuid.UUID
    text: str
    visible_to_client: bool
    author_id: uuid.UUID
    audit: AuditMetadata

    @staticmethod
    def from_entity(comment: Comment) -> "CommentResponse":
        return CommentResponse(
            id=comment.id, text=comment.texto, visible_to_client=comment.visivel_cliente,
            author_id=comment.usuario_id,
            # `comentarios` não tem nenhuma coluna de auditoria além de `criado_em` — nem
            # `criado_por` (o próprio `usuario_id` já é o autor). `updated_at` espelha `created_at`
            # mesmo depois de um `PATCH` real, porque não existe `atualizado_em` física para
            # refletir a edição (D400/D381-family, documentado em COLLABORATION_IMPLEMENTATION.md).
            audit=AuditMetadata(
                created_at=comment.criado_em, created_by=comment.usuario_id,
                updated_at=comment.criado_em, updated_by=comment.usuario_id,
            ),
        )
