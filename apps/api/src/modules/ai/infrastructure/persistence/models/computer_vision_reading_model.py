from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ComputerVisionReadingModel(Base):
    """`leituras_visao_computacional` (`relational/012-ia.md`). `ck_leituras_visao_computacional_
    confirmacao_humana` — reforço físico (audit 4): todo estado terminal que exigia revisão humana
    precisa de `usuario_confirmacao_id`, independente do que a Application faça. `inferencia_ia_id`
    sem FK física — mesmo motivo de `AIPredictionModel` (D202-style, `inferencias_ia` particionada
    não pode ser alvo de `UNIQUE(id)` isolado)."""

    __tablename__ = "leituras_visao_computacional"
    __table_args__ = (
        CheckConstraint(
            "status = 'PROCESSADA' OR revisao_humana_necessaria = FALSE OR usuario_confirmacao_id IS NOT NULL",
            name="ck_leituras_visao_computacional_confirmacao_humana",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    inferencia_ia_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    arquivo_origem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tipo_leitura: Mapped[str] = mapped_column(String, nullable=False)
    regiao_analisada: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    resultado_extraido: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    nivel_confianca: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    revisao_humana_necessaria: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PROCESSADA")
    usuario_confirmacao_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
