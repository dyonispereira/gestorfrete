from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Computed, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class FiscalEventModel(Base):
    """Mapeamento de `eventos_fiscais` (`relational/007-fiscal.md`) — log técnico bruto (D105),
    particionada por `data_hora_inicio` (D179), criada via SQL bruto na migration com uma partição
    `DEFAULT` (mesmo padrão de `logs_auditoria`/`leituras_hodometro`/`viagem_status_history`). PK
    composta `(id, data_hora_inicio)` — Postgres exige a coluna de partição em toda chave primária
    (a DDL em prosa de `relational/007-fiscal.md` simplifica para `id PRIMARY KEY`, mesma
    simplificação já feita nos outros três arquivos de particionamento e corrigida na migration
    real). `duracao_ms` é `GENERATED ALWAYS AS (...) STORED` — `sqlalchemy.Computed(...)` aplicado
    proativamente (reaplicação de D382, Lote 5)."""

    __tablename__ = "eventos_fiscais"
    __table_args__ = (
        Index("idx_eventos_fiscais_documento_tipo_documento_id", "documento_tipo", "documento_id"),
        # D201/D202-style: Postgres exige que toda constraint UNIQUE de uma tabela particionada
        # inclua a coluna de particionamento — `data_hora_inicio` entra na constraint física por
        # exigência do banco, não por relaxamento deliberado da regra de idempotência (D108/D111);
        # a aplicação (`FiscalInternalTransitions`) já verifica `exists_with_protocol` antes de
        # inserir, essa constraint é a segunda camada de defesa, não a única.
        Index(
            "uq_eventos_fiscais_documento_protocolo", "documento_tipo", "documento_id", "protocolo_externo",
            "data_hora_inicio", unique=True, postgresql_where=text("protocolo_externo IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    documento_tipo: Mapped[str] = mapped_column(String, nullable=False)
    documento_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tipo_evento: Mapped[str] = mapped_column(String, nullable=False)
    payload_arquivo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    protocolo_externo: Mapped[str | None] = mapped_column(String)
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    data_hora_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duracao_ms: Mapped[int | None] = mapped_column(
        Integer,
        Computed("EXTRACT(EPOCH FROM (data_hora_fim - data_hora_inicio)) * 1000"),
    )
    numero_tentativa: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    resultado: Mapped[str | None] = mapped_column(String)
    origem: Mapped[str] = mapped_column(String, nullable=False)
