from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class MobileSessionModel(Base):
    """Mapeamento de `sessoes_mobile` (D140). D407 — `id` sempre igual ao `Session.id`
    (`sessoes_acesso`) criado na mesma operação de login; nunca `gen_random_uuid()` independente
    (por isso não há `server_default` aqui, diferente do padrão usual — o valor é sempre passado
    explicitamente pela aplicação)."""

    __tablename__ = "sessoes_mobile"
    __table_args__ = (Index("idx_sessoes_mobile_motorista_id_status", "motorista_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    motorista_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("motoristas.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), nullable=False
    )
    dispositivo_mobile_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("dispositivos_mobile.id"), nullable=False
    )
    metodo_autenticacao: Mapped[str] = mapped_column(String, nullable=False)
    token_acesso_hash: Mapped[str] = mapped_column(String, nullable=False)
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_hora_expiracao_prevista: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_hora_encerramento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_encerramento: Mapped[str | None] = mapped_column(String)
    revogado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")
