from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Table, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base

# Junção N:N pura (relational/004-frota.md) — nunca Aggregate Root próprio, nunca soft delete
# (mesmo padrão de `usuarios_papeis`, Lote 2).
composicoes_veiculares_implementos = Table(
    "composicoes_veiculares_implementos",
    Base.metadata,
    Column("composicao_veicular_id", PG_UUID(as_uuid=True), ForeignKey("composicoes_veiculares.id"), primary_key=True),
    Column("implemento_id", PG_UUID(as_uuid=True), ForeignKey("implementos.id"), primary_key=True),
    Column("ordem", Integer, nullable=False),
)


class VehicleCompositionModel(Base):
    """Mapeamento de `composicoes_veiculares` — sem `criado_em`/`criado_por` (a DDL só tem
    `data_inicio_vigencia`/`data_fim_vigencia`/`alterado_por`, a própria vigência já é a
    auditoria temporal desta tabela, D037)."""

    __tablename__ = "composicoes_veiculares"
    __table_args__ = (
        CheckConstraint(
            "data_fim_vigencia IS NULL OR data_fim_vigencia > data_inicio_vigencia",
            name="ck_composicoes_veiculares_vigencia",
        ),
        Index(
            "uq_composicoes_veiculares_vigente",
            "veiculo_tracionador_id",
            unique=True,
            postgresql_where=text("data_fim_vigencia IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), nullable=False
    )
    tipo_combinacao: Mapped[str] = mapped_column(String, nullable=False)
    eixos_total: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="VALIDA")
    data_inicio_vigencia: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_fim_vigencia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    alterado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
