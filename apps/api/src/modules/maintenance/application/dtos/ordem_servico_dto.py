from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.maintenance.domain.entities.ordem_servico import OrdemServico


@dataclass(frozen=True)
class OrdemServicoDTO:
    id: uuid.UUID
    codigo: str
    veiculo_tracionador_id: uuid.UUID
    composicao_veicular_id: uuid.UUID | None
    fornecedor_executor_id: uuid.UUID | None
    tipo: str
    origem_abertura: str
    descricao_problema: str
    causa: str | None
    causa_raiz: str | None
    diagnostico_tecnico: str | None
    mecanico_id: uuid.UUID | None
    custo_previsto: Decimal | None
    custo_realizado: Decimal | None
    necessita_aprovacao: bool
    evidencia_conclusao_exigida: bool
    status: str
    data_inicio_execucao: datetime | None
    data_conclusao: datetime | None
    hodometro_abertura_km: Decimal | None
    hodometro_conclusao_km: Decimal | None
    criado_em: datetime
    criado_por: uuid.UUID | None
    atualizado_em: datetime
    atualizado_por: uuid.UUID | None

    @staticmethod
    def from_entity(entity: OrdemServico) -> "OrdemServicoDTO":
        return OrdemServicoDTO(
            id=entity.id, codigo=entity.codigo, veiculo_tracionador_id=entity.veiculo_tracionador_id,
            composicao_veicular_id=entity.composicao_veicular_id,
            fornecedor_executor_id=entity.fornecedor_executor_id, tipo=entity.tipo.value,
            origem_abertura=entity.origem_abertura.value, descricao_problema=entity.descricao_problema,
            causa=entity.causa.value if entity.causa else None, causa_raiz=entity.causa_raiz,
            diagnostico_tecnico=entity.diagnostico_tecnico, mecanico_id=entity.mecanico_id,
            custo_previsto=entity.custo_previsto, custo_realizado=entity.custo_realizado,
            necessita_aprovacao=entity.necessita_aprovacao,
            evidencia_conclusao_exigida=entity.evidencia_conclusao_exigida, status=entity.status.value,
            data_inicio_execucao=entity.data_inicio_execucao, data_conclusao=entity.data_conclusao,
            hodometro_abertura_km=entity.hodometro_abertura_km, hodometro_conclusao_km=entity.hodometro_conclusao_km,
            criado_em=entity.criado_em, criado_por=entity.criado_por, atualizado_em=entity.atualizado_em,
            atualizado_por=entity.atualizado_por,
        )
