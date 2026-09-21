from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.payment_method_dto import PaymentMethodDTO
from modules.financial.domain.value_objects.payment_method_status import PaymentMethodStatus
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payment_method_repository import (
    SqlAlchemyPaymentMethodRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdatePaymentMethodCommand(Command):
    actor: AuthenticatedActor
    payment_method_id: uuid.UUID
    nome: str | None
    status: PaymentMethodStatus | None


class UpdatePaymentMethodHandler(CommandHandler[UpdatePaymentMethodCommand, PaymentMethodDTO]):
    """`status: INATIVA` via `PATCH` é a única forma de "desativar" — sem `DELETE`, mesmo padrão de
    `CostCenter`/`ChartOfAccounts`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdatePaymentMethodCommand) -> PaymentMethodDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyPaymentMethodRepository(uow.session)

            payment_method = await repo.get_by_id(command.payment_method_id)
            if payment_method is None:
                raise NotFoundError("FINANCIAL_PAYMENT_METHOD_NOT_FOUND", "Forma de Pagamento não encontrada.")

            payment_method.update(nome=command.nome, status=command.status)
            await repo.add(payment_method)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="formas_pagamento",
                entidade_id=payment_method.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()

        return PaymentMethodDTO.from_entity(payment_method)
