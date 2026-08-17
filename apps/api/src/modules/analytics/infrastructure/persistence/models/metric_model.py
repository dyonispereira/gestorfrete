from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class MetricModel(Base):
    """Mapeamento de `metricas` (D150/D155/D419, `relational/011-bi.md`). Sem `UNIQUE(tenant_id,
    nome)` de propósito — cada versão é uma linha física própria (D419)."""

    __tablename__ = "metricas"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"))
    nome: Mapped[str] = mapped_column(String, nullable=False)
    formula: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    granularidade_temporal: Mapped[str] = mapped_column(String, nullable=False)
    granularidade_dimensional: Mapped[str] = mapped_column(String, nullable=False)
    unidade: Mapped[str] = mapped_column(String, nullable=False)
    origem_dados: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    periodicidade_calculo: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")
