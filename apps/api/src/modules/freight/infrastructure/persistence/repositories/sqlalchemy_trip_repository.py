from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.freight.domain.entities.trip import Trip
from modules.freight.domain.repositories.trip_repository import TripRepository
from modules.freight.domain.value_objects.trip_financial_status import TripFinancialStatus
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus
from modules.freight.domain.value_objects.trip_operational_status import TripOperationalStatus
from modules.freight.infrastructure.persistence.models.trip_model import TripModel
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.specification import Specification


def _to_entity(model: TripModel) -> Trip:
    return Trip(
        id=model.id,
        codigo=model.codigo,
        cliente_id=model.cliente_id,
        motorista_id=model.motorista_id,
        veiculo_tracionador_id=model.veiculo_tracionador_id,
        data_programada=model.data_programada,
        janela_programada=model.janela_programada,
        status_operacional=TripOperationalStatus(model.status_operacional),
        status_fiscal=TripFiscalStatus(model.status_fiscal),
        status_financeiro=TripFinancialStatus(model.status_financeiro),
        nome_motorista_snapshot=model.nome_motorista_snapshot,
        placa_veiculo_snapshot=model.placa_veiculo_snapshot,
        cliente_snapshot=model.cliente_snapshot,
        receita_prevista_snapshot=model.receita_prevista_snapshot,
        tabela_preco_aplicada_snapshot_id=model.tabela_preco_aplicada_snapshot_id,
        custo_previsto=model.custo_previsto,
        custo_realizado=model.custo_realizado,
        receita_realizada=model.receita_realizada,
        margem_realizada=model.margem_realizada,
        desvio_financeiro=model.desvio_financeiro,
        km_rodado=model.km_rodado,
        encerrada=model.encerrada,
        margem_prevista=model.margem_prevista,
        audit=AuditMetadata(
            created_at=model.criado_em,
            created_by=model.criado_por,
            updated_at=model.atualizado_em,
            updated_by=model.atualizado_por,
            deleted_at=model.excluido_em,
            deleted_by=model.excluido_por,
        ),
    )


class SqlAlchemyTripRepository(TripRepository):
    """`encerrada`/`margem_prevista` nunca aparecem em `INSERT`/`UPDATE` — são `GENERATED` no
    Postgres (D019/D185). `add()` sempre recarrega as duas do banco logo após `flush()` e as
    atribui de volta na entidade em memória, para que o DTO devolvido ao chamador (D238) nunca
    fique obsoleto."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Trip | None:
        tenant_id = get_current_tenant_id()
        stmt = select(TripModel).where(
            TripModel.id == id, TripModel.tenant_id == tenant_id, TripModel.excluido_em.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def client_exists(self, cliente_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(ClientModel.id).where(
            ClientModel.id == cliente_id, ClientModel.tenant_id == tenant_id, ClientModel.excluido_em.is_(None)
        )
        return (await self._session.execute(stmt)).first() is not None

    async def get_client_snapshot(self, cliente_id: uuid.UUID) -> dict[str, Any] | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ClientModel).where(ClientModel.id == cliente_id, ClientModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return {"razao_social": model.razao_social, "nome_fantasia": model.nome_fantasia, "cnpj_cpf": model.cnpj_cpf}

    async def list_page(
        self,
        *,
        page: int,
        limit: int,
        status_operacional: str | None,
        status_fiscal: str | None,
        status_financeiro: str | None,
        motorista_id: uuid.UUID | None,
        veiculo_id: uuid.UUID | None,
        cliente_id: uuid.UUID | None,
        data_programada: date | None,
        codigo: str | None,
    ) -> tuple[list[Trip], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(TripModel).where(TripModel.tenant_id == tenant_id, TripModel.excluido_em.is_(None))
        if status_operacional is not None:
            stmt = stmt.where(TripModel.status_operacional == status_operacional)
        if status_fiscal is not None:
            stmt = stmt.where(TripModel.status_fiscal == status_fiscal)
        if status_financeiro is not None:
            stmt = stmt.where(TripModel.status_financeiro == status_financeiro)
        if motorista_id is not None:
            stmt = stmt.where(TripModel.motorista_id == motorista_id)
        if veiculo_id is not None:
            stmt = stmt.where(TripModel.veiculo_tracionador_id == veiculo_id)
        if cliente_id is not None:
            stmt = stmt.where(TripModel.cliente_id == cliente_id)
        if data_programada is not None:
            stmt = stmt.where(TripModel.data_programada == data_programada)
        if codigo is not None:
            stmt = stmt.where(TripModel.codigo == codigo)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(TripModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: Trip) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(TripModel, aggregate.id)
        if model is None:
            model = TripModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.cliente_id = aggregate.cliente_id
        model.motorista_id = aggregate.motorista_id
        model.veiculo_tracionador_id = aggregate.veiculo_tracionador_id
        model.data_programada = aggregate.data_programada
        model.janela_programada = aggregate.janela_programada
        model.status_operacional = aggregate.status_operacional.value
        model.status_fiscal = aggregate.status_fiscal.value
        model.status_financeiro = aggregate.status_financeiro.value
        model.nome_motorista_snapshot = aggregate.nome_motorista_snapshot
        model.placa_veiculo_snapshot = aggregate.placa_veiculo_snapshot
        model.cliente_snapshot = aggregate.cliente_snapshot
        model.receita_prevista_snapshot = aggregate.receita_prevista_snapshot
        model.tabela_preco_aplicada_snapshot_id = aggregate.tabela_preco_aplicada_snapshot_id
        model.custo_previsto = aggregate.custo_previsto
        model.custo_realizado = aggregate.custo_realizado
        model.receita_realizada = aggregate.receita_realizada
        model.margem_realizada = aggregate.margem_realizada
        model.desvio_financeiro = aggregate.desvio_financeiro
        model.km_rodado = aggregate.km_rodado
        model.criado_em = aggregate.audit.created_at
        model.criado_por = aggregate.audit.created_by
        model.atualizado_em = aggregate.audit.updated_at
        model.atualizado_por = aggregate.audit.updated_by
        model.excluido_em = aggregate.audit.deleted_at
        model.excluido_por = aggregate.audit.deleted_by
        # `encerrada`/`margem_prevista` nunca atribuídas ao model (GENERATED, D019/D185) — recarregadas
        # do banco após o flush para a entidade em memória nunca ficar obsoleta (D238).
        await self._session.flush()
        await self._session.refresh(model)
        aggregate.encerrada = model.encerrada
        aggregate.margem_prevista = model.margem_prevista

    async def find(self, specification: Specification[Trip]) -> list[Trip]:
        raise NotImplementedError("Use list_page — filtros de Trip são resolvidos via SQL")
