from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.maintenance.domain.entities.ordem_servico import OrdemServico
from modules.maintenance.domain.repositories.ordem_servico_repository import OrdemServicoRepository
from modules.maintenance.domain.value_objects.ordem_servico_causa import OrdemServicoCausa
from modules.maintenance.domain.value_objects.ordem_servico_origem_abertura import OrdemServicoOrigemAbertura
from modules.maintenance.domain.value_objects.ordem_servico_status import OrdemServicoStatus
from modules.maintenance.domain.value_objects.ordem_servico_tipo import OrdemServicoTipo
from modules.maintenance.infrastructure.persistence.models.ordem_servico_model import OrdemServicoModel
from shared_kernel.domain.specification import Specification


def _to_entity(model: OrdemServicoModel) -> OrdemServico:
    return OrdemServico(
        id=model.id, codigo=model.codigo, veiculo_tracionador_id=model.veiculo_tracionador_id,
        composicao_veicular_id=model.composicao_veicular_id, fornecedor_executor_id=model.fornecedor_executor_id,
        tipo=OrdemServicoTipo(model.tipo), origem_abertura=OrdemServicoOrigemAbertura(model.origem_abertura),
        descricao_problema=model.descricao_problema,
        causa=OrdemServicoCausa(model.causa) if model.causa else None, causa_raiz=model.causa_raiz,
        diagnostico_tecnico=model.diagnostico_tecnico, mecanico_id=model.mecanico_id,
        custo_previsto=model.custo_previsto, custo_realizado=model.custo_realizado,
        necessita_aprovacao=model.necessita_aprovacao, evidencia_conclusao_exigida=model.evidencia_conclusao_exigida,
        status=OrdemServicoStatus(model.status), data_inicio_execucao=model.data_inicio_execucao,
        data_conclusao=model.data_conclusao, hodometro_abertura_km=model.hodometro_abertura_km,
        hodometro_conclusao_km=model.hodometro_conclusao_km, criado_em=model.criado_em, criado_por=model.criado_por,
        atualizado_em=model.atualizado_em, atualizado_por=model.atualizado_por,
    )


class SqlAlchemyOrdemServicoRepository(OrdemServicoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> OrdemServico | None:
        tenant_id = get_current_tenant_id()
        stmt = select(OrdemServicoModel).where(OrdemServicoModel.id == id, OrdemServicoModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, veiculo_tracionador_id: uuid.UUID | None, tipo: str | None,
        status: str | None,
    ) -> tuple[list[OrdemServico], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(OrdemServicoModel).where(OrdemServicoModel.tenant_id == tenant_id)
        if veiculo_tracionador_id is not None:
            stmt = stmt.where(OrdemServicoModel.veiculo_tracionador_id == veiculo_tracionador_id)
        if tipo is not None:
            stmt = stmt.where(OrdemServicoModel.tipo == tipo)
        if status is not None:
            stmt = stmt.where(OrdemServicoModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(OrdemServicoModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, aggregate: OrdemServico) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(OrdemServicoModel, aggregate.id)
        if model is None:
            model = OrdemServicoModel(id=aggregate.id, tenant_id=tenant_id)
            self._session.add(model)
        model.codigo = aggregate.codigo
        model.veiculo_tracionador_id = aggregate.veiculo_tracionador_id
        model.composicao_veicular_id = aggregate.composicao_veicular_id
        model.fornecedor_executor_id = aggregate.fornecedor_executor_id
        model.tipo = aggregate.tipo.value
        model.origem_abertura = aggregate.origem_abertura.value
        model.descricao_problema = aggregate.descricao_problema
        model.causa = aggregate.causa.value if aggregate.causa else None
        model.causa_raiz = aggregate.causa_raiz
        model.diagnostico_tecnico = aggregate.diagnostico_tecnico
        model.mecanico_id = aggregate.mecanico_id
        model.custo_previsto = aggregate.custo_previsto
        model.custo_realizado = aggregate.custo_realizado
        model.necessita_aprovacao = aggregate.necessita_aprovacao
        model.evidencia_conclusao_exigida = aggregate.evidencia_conclusao_exigida
        model.status = aggregate.status.value
        model.data_inicio_execucao = aggregate.data_inicio_execucao
        model.data_conclusao = aggregate.data_conclusao
        model.hodometro_abertura_km = aggregate.hodometro_abertura_km
        model.hodometro_conclusao_km = aggregate.hodometro_conclusao_km
        model.criado_em = aggregate.criado_em
        model.criado_por = aggregate.criado_por
        model.atualizado_em = aggregate.atualizado_em
        model.atualizado_por = aggregate.atualizado_por
        await self._session.flush()

    async def find(self, specification: Specification[OrdemServico]) -> list[OrdemServico]:
        raise NotImplementedError("Use list_page — filtros de OrdemServico são resolvidos via SQL")
