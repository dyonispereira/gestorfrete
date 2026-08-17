from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TrackingEquipmentModel(Base):
    """Mapeamento de `equipamentos_rastreamento` (D128). `uq_equipamentos_rastreamento_principal_
    vigente` (índice único parcial) garante fisicamente no máximo um `PRINCIPAL` vigente por
    veículo — a Auditoria #6 do usuário testa exatamente esta constraint."""

    __tablename__ = "equipamentos_rastreamento"
    __table_args__ = (
        UniqueConstraint("identificador_serial", name="uq_equipamentos_rastreamento_identificador_serial"),
        CheckConstraint(
            "data_fim_vigencia IS NULL OR data_inicio_vigencia IS NULL OR data_fim_vigencia > data_inicio_vigencia",
            name="ck_equipamentos_rastreamento_vigencia",
        ),
        Index(
            "uq_equipamentos_rastreamento_principal_vigente", "veiculo_tracionador_id", unique=True,
            postgresql_where=text("tipo_equipamento = 'PRINCIPAL' AND data_fim_vigencia IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    provedor_rastreamento_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provedores_rastreamento.id"), nullable=False
    )
    identificador_serial: Mapped[str] = mapped_column(String, nullable=False)
    tipo_equipamento: Mapped[str] = mapped_column(String, nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id")
    )
    data_inicio_vigencia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_fim_vigencia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    alterado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
