from __future__ import annotations

from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.financial.application.dtos.payment_method_dto import PaymentMethodDTO
from modules.financial.domain.entities.payment_method import PaymentMethod
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payment_method_repository import (
    SqlAlchemyPaymentMethodRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreatePaymentMethodCommand(Command):
    actor: AuthenticatedActor
    nome: str


class CreatePaymentMethodHandler(CommandHandler[CreatePaymentMethodCommand, PaymentMethodDTO]):
    """D386 — fecha o gap de exposição HTTP (Lote Financeiro, Parte 2.1). Entidade/Repository já
    existiam, só faltava este comando/rota; `uq_formas_pagamento_tenant_id_nome` já protegia contra
    duplicidade no schema, aqui só devolve um erro de domínio claro antes do IntegrityError."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreatePaymentMethodCommand) -> PaymentMethodDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyPaymentMethodRepository(uow.session)

            if await repo.exists_with_nome(command.nome):
                raise ConflictError(
                    "FINANCIAL_PAYMENT_METHOD_NAME_ALREADY_EXISTS",
                    "Já existe uma Forma de Pagamento com este nome neste tenant.",
                )

            payment_method = PaymentMethod.create(nome=command.nome)
            await repo.add(payment_method)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="formas_pagamento",
                entidade_id=payment_method.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"nome": payment_method.nome},
            )

            await uow.commit()

        return PaymentMethodDTO.from_entity(payment_method)
