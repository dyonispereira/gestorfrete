from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.accounts_receivable import AccountsReceivable
from modules.financial.domain.repositories.accounts_receivable_repository import AccountsReceivableRepository
from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from modules.financial.infrastructure.persistence.models.accounts_receivable_model import AccountsReceivableModel
from modules.financial.infrastructure.persistence.models.invoice_model import InvoiceModel


def _to_entity(model: AccountsReceivableModel) -> AccountsReceivable:
    return AccountsReceivable(
        id=model.id, fatura_id=model.fatura_id, numero_parcela=model.numero_parcela, valor=model.valor,
        valor_recebido=model.valor_recebido, data_vencimento=model.data_vencimento, competencia=model.competencia,
        data_recebimento=model.data_recebimento, status=ReceivableStatus(model.status),
    )


class SqlAlchemyAccountsReceivableRepository(AccountsReceivableRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> AccountsReceivable | None:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsReceivableModel).where(
            AccountsReceivableModel.id == id, AccountsReceivableModel.tenant_id == tenant_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_invoice(self, fatura_id: uuid.UUID) -> list[AccountsReceivable]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(AccountsReceivableModel)
            .where(AccountsReceivableModel.tenant_id == tenant_id, AccountsReceivableModel.fatura_id == fatura_id)
            .order_by(AccountsReceivableModel.numero_parcela)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def exists_with_installment(self, fatura_id: uuid.UUID, numero_parcela: int) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsReceivableModel.id).where(
            AccountsReceivableModel.tenant_id == tenant_id, AccountsReceivableModel.fatura_id == fatura_id,
            AccountsReceivableModel.numero_parcela == numero_parcela,
        )
        return (await self._session.execute(stmt)).first() is not None

    async def count_pending_for_invoice(self, fatura_id: uuid.UUID, *, excluding_id: uuid.UUID | None = None) -> int:
        """Conta parcelas ainda com saldo em aberto — inclui `PARCIALMENTE_RECEBIDO` (Lote
        Financeiro, Parte 2.1): uma Fatura com qualquer parcela parcialmente recebida não está
        `RECEBIDA` por completo, mesmo que nenhuma parcela esteja 100% pendente."""
        tenant_id = get_current_tenant_id()
        stmt = select(AccountsReceivableModel.id).where(
            AccountsReceivableModel.tenant_id == tenant_id, AccountsReceivableModel.fatura_id == fatura_id,
            AccountsReceivableModel.status.in_([
                ReceivableStatus.PENDENTE.value, ReceivableStatus.VENCIDA.value,
                ReceivableStatus.PARCIALMENTE_RECEBIDO.value,
            ]),
        )
        if excluding_id is not None:
            stmt = stmt.where(AccountsReceivableModel.id != excluding_id)
        return len((await self._session.execute(stmt)).all())

    async def sum_received_for_invoice(self, fatura_id: uuid.UUID) -> Decimal:
        """Soma `valor_recebido` (não `valor`) — Receita Realizada da Viagem precisa refletir o
        que foi de fato recebido, inclusive baixas parciais (Lote Financeiro, Parte 2.1). Uma
        parcela `RECEBIDA`/`CONCILIADA` sempre tem `valor_recebido == valor` (invariante da
        própria `receive_payment`), então isso não muda o comportamento anterior para o caso
        cheio — só passa a contar `PARCIALMENTE_RECEBIDO` corretamente também."""
        tenant_id = get_current_tenant_id()
        stmt = select(func.coalesce(func.sum(AccountsReceivableModel.valor_recebido), 0)).where(
            AccountsReceivableModel.tenant_id == tenant_id, AccountsReceivableModel.fatura_id == fatura_id,
            AccountsReceivableModel.status.in_([
                ReceivableStatus.RECEBIDA.value, ReceivableStatus.CONCILIADA.value,
                ReceivableStatus.PARCIALMENTE_RECEBIDO.value,
            ]),
        )
        total = (await self._session.execute(stmt)).scalar_one()
        return Decimal(total)

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status: str | None,
        client_id: uuid.UUID | None,
        accounting_period: date | None,
        due_date_from: date | None,
        due_date_to: date | None,
    ) -> tuple[list[tuple[AccountsReceivable, uuid.UUID]], int]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(AccountsReceivableModel, InvoiceModel.cliente_id)
            .join(InvoiceModel, InvoiceModel.id == AccountsReceivableModel.fatura_id)
            .where(AccountsReceivableModel.tenant_id == tenant_id)
        )
        if client_id is not None:
            stmt = stmt.where(InvoiceModel.cliente_id == client_id)
        if accounting_period is not None:
            stmt = stmt.where(AccountsReceivableModel.competencia == accounting_period)
        if due_date_from is not None:
            stmt = stmt.where(AccountsReceivableModel.data_vencimento >= due_date_from)
        if due_date_to is not None:
            stmt = stmt.where(AccountsReceivableModel.data_vencimento <= due_date_to)
        if status is not None:
            # `VENCIDA` nunca é persistida (`AccountsReceivable.effective_status` é derivada de
            # `PENDENTE` + `data_vencimento` na leitura, nunca uma coluna própria) — mesmo
            # raciocínio replicado aqui em SQL para o filtro bater com o que a entidade mostra.
            today = datetime.now(timezone.utc).date()
            if status == ReceivableStatus.VENCIDA.value:
                stmt = stmt.where(
                    AccountsReceivableModel.status == ReceivableStatus.PENDENTE.value,
                    AccountsReceivableModel.data_vencimento < today,
                )
            elif status == ReceivableStatus.PENDENTE.value:
                stmt = stmt.where(
                    AccountsReceivableModel.status == ReceivableStatus.PENDENTE.value,
                    AccountsReceivableModel.data_vencimento >= today,
                )
            else:
                stmt = stmt.where(AccountsReceivableModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AccountsReceivableModel.data_vencimento.asc()).offset((page - 1) * limit).limit(limit)
        rows = (await self._session.execute(stmt)).all()
        return [(_to_entity(model), cliente_id) for model, cliente_id in rows], total

    async def add(self, receivable: AccountsReceivable) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(AccountsReceivableModel, receivable.id)
        if model is None:
            model = AccountsReceivableModel(id=receivable.id, tenant_id=tenant_id, fatura_id=receivable.fatura_id)
            self._session.add(model)
        model.numero_parcela = receivable.numero_parcela
        model.valor = receivable.valor
        model.valor_recebido = receivable.valor_recebido
        model.data_vencimento = receivable.data_vencimento
        model.competencia = receivable.competencia
        model.data_recebimento = receivable.data_recebimento
        model.status = receivable.status.value
        await self._session.flush()
