from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class VehicleDocumentModel(Base):
    """Mapeamento de `documentos_veiculo` — sem colunas de timestamp (a DDL não as tem).
    `arquivo_id` sem FK física (`arquivos`/`storage` não implementado, mesma situação de
    `documentos_motorista.arquivo_id`, Lote 3)."""

    __tablename__ = "documentos_veiculo"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    numero: Mapped[str] = mapped_column(String, nullable=False)
    data_validade: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="VALIDO")
    arquivo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
