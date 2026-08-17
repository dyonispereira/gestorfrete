from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TripAllocationModel(Base):
    """Mapeamento de `alocacoes_recurso_viagem` (D188, `relational/003-operacao.md`). Índice único
    parcial reforça "exatamente uma `VIGENTE` por Viagem" — mesmo padrão de
    `uq_composicoes_veiculares_vigente` (Lote 4)."""

    __tablename__ = "alocacoes_recurso_viagem"
    __table_args__ = (
        Index(
            "uq_alocacoes_recurso_viagem_vigente", "viagem_id", unique=True, postgresql_where=text("status = 'VIGENTE'")
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    motorista_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("motoristas.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), nullable=False
    )
    implemento_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("implementos.id"))
    status: Mapped[str] = mapped_column(String, nullable=False, default="VIGENTE")
    motivo_troca: Mapped[str | None] = mapped_column(String)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
