from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AIClassificationModel(Base):
    """`classificacoes_ia` (`relational/012-ia.md`) — Enum fechado (Risco/Prioridade/Gravidade);
    Anomalia é `anomalias_detectadas`, tabela própria (reconciliação já feita no Domain).
    `inferencia_ia_id` sem FK física — mesmo motivo de `AIPredictionModel` (D202-style, `inferencias_
    ia` particionada não pode ser alvo de `UNIQUE(id)` isolado)."""

    __tablename__ = "classificacoes_ia"
    __table_args__ = (
        Index(
            "idx_classificacoes_ia_entidade_alvo", "entidade_alvo_tipo", "entidade_alvo_id",
            "tipo_classificacao",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    inferencia_ia_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tipo_classificacao: Mapped[str] = mapped_column(String, nullable=False)
    entidade_alvo_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidade_alvo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    rotulo: Mapped[str] = mapped_column(String, nullable=False)
    nivel_confianca: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
