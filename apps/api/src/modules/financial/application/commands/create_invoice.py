from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, ValidationError
from modules.crm.infrastructure.persistence.repositories.sqlalchemy_client_repository import (
    SqlAlchemyClientRepository,
)
from modules.financial.application.dtos.invoice_dto import InvoiceDTO
from modules.financial.domain.entities.accounts_receivable import AccountsReceivable
from modules.financial.domain.entities.invoice import Invoice
from modules.financial.domain.entities.receivable_status_history_entry import ReceivableStatusHistoryEntry
from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_receivable_repository import (
    SqlAlchemyAccountsReceivableRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_repository import (
    SqlAlchemyInvoiceRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_payment_method_repository import (
    SqlAlchemyPaymentMethodRepository,
)
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_receivable_status_history_repository import (
    SqlAlchemyReceivableStatusHistoryRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.domain.value_objects.trip_financial_status import TripFinancialStatus
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_proof_of_delivery_repository import (
    SqlAlchemyProofOfDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata

_FISCAL_STATUSES_ALLOWING_INVOICE = frozenset(
    {TripFiscalStatus.CTE_EMITIDO, TripFiscalStatus.MDFE_EMITIDO, TripFiscalStatus.MDFE_ENCERRADO}
)


@dataclass(frozen=True)
class InvoiceInstallmentInput:
    value: Decimal
    due_date: date


@dataclass(frozen=True)
class CreateInvoiceCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID | None
    delivery_id: uuid.UUID | None
    client_id: uuid.UUID
    total_value: Decimal
    payment_method_id: uuid.UUID
    installments: list[InvoiceInstallmentInput]


class CreateInvoiceHandler(CommandHandler[CreateInvoiceCommand, InvoiceDTO]):
    """D388 — precondição ("Canhoto registrado e CT-e emitido") checada por leitura cross-module
    real contra `freight` (Lote 5), nunca simulada. D390 — dispara
    `TripInternalTransitions.record_financial_transition(FATURADA)` quando `trip_id` presente."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateInvoiceCommand) -> InvoiceDTO:
        Invoice.check_origin(viagem_id=command.trip_id, entrega_id=command.delivery_id)

        async with SQLAlchemyUnitOfWork() as uow:
            invoice_repo = SqlAlchemyInvoiceRepository(uow.session)
            receivable_repo = SqlAlchemyAccountsReceivableRepository(uow.session)
            receivable_history_repo = SqlAlchemyReceivableStatusHistoryRepository(uow.session)
            client_repo = SqlAlchemyClientRepository(uow.session)
            payment_method_repo = SqlAlchemyPaymentMethodRepository(uow.session)
            trip_repo = SqlAlchemyTripRepository(uow.session)
            delivery_repo = SqlAlchemyDeliveryRepository(uow.session)
            pod_repo = SqlAlchemyProofOfDeliveryRepository(uow.session)

            if await client_repo.get_by_id(command.client_id) is None:
                raise ValidationError("FINANCIAL_UNKNOWN_CLIENT_ID", "Cliente inexistente.")
            if await payment_method_repo.get_by_id(command.payment_method_id) is None:
                raise ValidationError("FINANCIAL_UNKNOWN_PAYMENT_METHOD_ID", "Forma de Pagamento inexistente.")

            if command.trip_id is not None:
                trip = await trip_repo.get_by_id(command.trip_id)
                if trip is None:
                    raise ValidationError("FINANCIAL_UNKNOWN_TRIP_ID", "Viagem inexistente.")

                deliveries = await delivery_repo.list_for_trip(command.trip_id)
                has_pod = False
                for delivery in deliveries:
                    if await pod_repo.exists_for_delivery(delivery.id):
                        has_pod = True
                        break
                cte_emitted = trip.status_fiscal in _FISCAL_STATUSES_ALLOWING_INVOICE
                if not has_pod or not cte_emitted:
                    raise ConflictError(
                        "FINANCIAL_INVOICE_MISSING_PRECONDITION",
                        "Faturamento exige ao menos um Canhoto registrado e CT-e emitido para a viagem.",
                    )
            elif command.delivery_id is not None and await delivery_repo.get_by_id(command.delivery_id) is None:
                raise ValidationError("FINANCIAL_UNKNOWN_DELIVERY_ID", "Entrega inexistente.")

            now = datetime.now(timezone.utc)
            numero_fatura = f"FAT-{now.year}-{uuid.uuid4().hex[:8].upper()}"
            invoice = Invoice.create(
                numero_fatura=numero_fatura, viagem_id=command.trip_id, entrega_id=command.delivery_id,
                cliente_id=command.client_id, valor_total=command.total_value, data_emissao=now.date(),
                forma_pagamento_id=command.payment_method_id,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await invoice_repo.add(invoice)

            for index, installment in enumerate(command.installments, start=1):
                receivable = AccountsReceivable.create(
                    fatura_id=invoice.id, numero_parcela=index, valor=installment.value,
                    data_vencimento=installment.due_date,
                )
                await receivable_repo.add(receivable)
                await receivable_history_repo.add(
                    ReceivableStatusHistoryEntry.create(
                        conta_receber_id=receivable.id, status=ReceivableStatus.PENDENTE,
                        usuario_id=command.actor.user_id, now=now,
                    )
                )

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="faturas", entidade_id=invoice.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"numero_fatura": invoice.numero_fatura, "valor_total": str(invoice.valor_total)},
            )

            await uow.commit()

        if command.trip_id is not None:
            await TripInternalTransitions().record_financial_transition(
                trip_id=command.trip_id, status=TripFinancialStatus.FATURADA, now=now
            )

        return InvoiceDTO.from_entity(invoice)
