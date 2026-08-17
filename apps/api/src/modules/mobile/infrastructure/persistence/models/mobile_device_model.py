from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class MobileDeviceModel(Base):
    """Mapeamento de `dispositivos_mobile`. `identificador_dispositivo` único globalmente (D084)."""

    __tablename__ = "dispositivos_mobile"
    __table_args__ = (
        UniqueConstraint("identificador_dispositivo", name="uq_dispositivos_mobile_identificador"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    motorista_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("motoristas.id"), nullable=False)
    identificador_dispositivo: Mapped[str] = mapped_column(String, nullable=False)
    sistema_operacional: Mapped[str] = mapped_column(String, nullable=False)
    versao_so: Mapped[str | None] = mapped_column(String)
    versao_app: Mapped[str] = mapped_column(String, nullable=False)
    token_push: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
    ultimo_acesso_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
