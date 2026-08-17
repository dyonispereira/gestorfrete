from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AIPredictionModel(Base):
    """`predicoes_ia` (`relational/012-ia.md`) — D163, sempre com período de validade.
    `inferencia_ia_id` sem FK física (D202-style): Postgres exige que TODA constraint `UNIQUE`
    (não só a PK) de uma tabela particionada inclua a coluna de partição — `inferencias_ia` é
    particionada por `data_hora_inicio`, então um `UNIQUE(id)` isolado é fisicamente impossível.
    Integridade referencial garantida pela aplicação (`AIInferenceEngine` sempre cria a Inferência
    antes da saída, na mesma transação), nunca pelo banco."""

    __tablename__ = "predicoes_ia"
    __table_args__ = (
        Index("idx_predicoes_ia_entidade_alvo", "entidade_alvo_tipo", "entidade_alvo_id"),
        Index("idx_predicoes_ia_status_validade", "status", "data_hora_validade_fim"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    inferencia_ia_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    categoria: Mapped[str] = mapped_column(String, nullable=False)
    entidade_alvo_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidade_alvo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    valor_previsto: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    nivel_confianca: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    data_hora_validade_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATUAL")
