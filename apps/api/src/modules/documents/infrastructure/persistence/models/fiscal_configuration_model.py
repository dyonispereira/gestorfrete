from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class FiscalConfigurationModel(Base):
    """Mapeamento de `configuracoes_fiscais_tenant` (D110) — única fonte de numeração de CT-e/
    MDF-e. Singular por tenant. D400 — sem `audit` (DDL congelada não tem nenhuma coluna de
    timestamp)."""

    __tablename__ = "configuracoes_fiscais_tenant"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_configuracoes_fiscais_tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    certificado_arquivo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    certificado_validade: Mapped[date] = mapped_column(Date, nullable=False)
    ambiente: Mapped[str] = mapped_column(String, nullable=False, default="HOMOLOGACAO")
    regime_tributario: Mapped[str] = mapped_column(String, nullable=False)
    serie_cte: Mapped[str] = mapped_column(String, nullable=False)
    proximo_numero_cte: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    serie_mdfe: Mapped[str] = mapped_column(String, nullable=False)
    proximo_numero_mdfe: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")
