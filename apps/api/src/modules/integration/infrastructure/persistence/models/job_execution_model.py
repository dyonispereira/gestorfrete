from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class JobExecutionModel(Base):
    """Mapeamento de `execucoes_job` (D037, `relational/010-administracao.md`) — particionada
    mensalmente por `data_hora_inicio` no schema congelado; mapeada aqui como tabela lógica única
    (mesmo padrão já usado para `eventos_fiscais`/`logs_auditoria` no ORM, a partição física é
    resolvida pelo Postgres, nunca pelo SQLAlchemy)."""

    __tablename__ = "execucoes_job"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"))
    tipo_job: Mapped[str] = mapped_column(String, nullable=False)
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, primary_key=True)
    data_hora_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resultado: Mapped[str | None] = mapped_column(String)
