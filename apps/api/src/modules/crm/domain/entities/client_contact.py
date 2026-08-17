from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_entity import BaseEntity


class ClientContact(BaseEntity[uuid.UUID]):
    """Não-Aggregate-Root — lido/salvo pelo seu próprio Repository, nunca carregado dentro do
    objeto Python `Client` (`CLIENT_IMPLEMENTATION.md`). `contatos_cliente` não tem
    `criado_por`/`atualizado_por`/`excluido_por` (D217 — a auditoria reflete exatamente o que a
    tabela tem, nunca inventa um campo, `012-contacts.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        cliente_id: uuid.UUID,
        nome: str,
        cargo: str | None,
        telefone: str | None,
        email: str | None,
        created_at: datetime,
        updated_at: datetime,
        deleted_at: datetime | None,
    ) -> None:
        super().__init__(id)
        self.cliente_id = cliente_id
        self.nome = nome
        self.cargo = cargo
        self.telefone = telefone
        self.email = email
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        *,
        cliente_id: uuid.UUID,
        nome: str,
        cargo: str | None,
        telefone: str | None,
        email: str | None,
        now: datetime,
    ) -> "ClientContact":
        return cls(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            nome=nome,
            cargo=cargo,
            telefone=telefone,
            email=email,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def update(self, *, nome: str | None, cargo: str | None, telefone: str | None, email: str | None, now: datetime) -> None:
        if nome is not None:
            self.nome = nome
        if cargo is not None:
            self.cargo = cargo
        if telefone is not None:
            self.telefone = telefone
        if email is not None:
            self.email = email
        self.updated_at = now

    def soft_delete(self, *, now: datetime) -> None:
        self.deleted_at = now
        self.updated_at = now
