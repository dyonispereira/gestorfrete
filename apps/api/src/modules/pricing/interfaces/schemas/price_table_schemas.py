from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from modules.pricing.application.dtos.price_table_dto import PriceTableDTO, PriceTableItemDTO
from modules.pricing.domain.value_objects.faixa_distancia_mode import FaixaDistanciaMode
from modules.pricing.domain.value_objects.price_table_direction import PriceTableDirection
from modules.pricing.domain.value_objects.price_table_unit import PriceTableUnit


class PriceTableResponse(BaseModel):
    id: uuid.UUID
    nome: str
    direcao: PriceTableDirection
    versao: int
    vigencia_inicio: date
    vigencia_fim: date | None
    cliente_id: uuid.UUID | None
    status: str
    created_at: datetime
    created_by: uuid.UUID | None
    updated_at: datetime
    updated_by: uuid.UUID | None

    @staticmethod
    def from_dto(dto: PriceTableDTO) -> "PriceTableResponse":
        return PriceTableResponse(
            id=dto.id, nome=dto.nome, direcao=PriceTableDirection(dto.direcao), versao=dto.versao,
            vigencia_inicio=dto.vigencia_inicio, vigencia_fim=dto.vigencia_fim, cliente_id=dto.cliente_id,
            status=dto.status, created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at,
            updated_by=dto.updated_by,
        )


class PriceTableItemResponse(BaseModel):
    id: uuid.UUID
    tabela_preco_id: uuid.UUID
    unidade_calculo: PriceTableUnit
    categoria_veiculo_id: uuid.UUID | None
    origem_uf: str | None
    destino_uf: str | None
    faixa_distancia_min_km: Decimal | None
    faixa_distancia_max_km: Decimal | None
    faixa_modo: FaixaDistanciaMode | None
    valor: Decimal
    valor_minimo: Decimal | None
    adicional_fixo: Decimal | None
    desconto_fixo: Decimal | None
    adicional_percentual: Decimal | None
    desconto_percentual: Decimal | None
    base_percentual_descricao: str | None
    created_at: datetime

    @staticmethod
    def from_dto(dto: PriceTableItemDTO) -> "PriceTableItemResponse":
        return PriceTableItemResponse(
            id=dto.id, tabela_preco_id=dto.tabela_preco_id, unidade_calculo=PriceTableUnit(dto.unidade_calculo),
            categoria_veiculo_id=dto.categoria_veiculo_id, origem_uf=dto.origem_uf, destino_uf=dto.destino_uf,
            faixa_distancia_min_km=dto.faixa_distancia_min_km, faixa_distancia_max_km=dto.faixa_distancia_max_km,
            faixa_modo=FaixaDistanciaMode(dto.faixa_modo) if dto.faixa_modo else None, valor=dto.valor,
            valor_minimo=dto.valor_minimo, adicional_fixo=dto.adicional_fixo, desconto_fixo=dto.desconto_fixo,
            adicional_percentual=dto.adicional_percentual, desconto_percentual=dto.desconto_percentual,
            base_percentual_descricao=dto.base_percentual_descricao, created_at=dto.created_at,
        )


class CreatePriceTableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str
    direcao: PriceTableDirection
    vigencia_inicio: date
    vigencia_fim: date | None = None
    cliente_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _cliente_only_for_venda(self) -> "CreatePriceTableRequest":
        if self.direcao == PriceTableDirection.COMPRA and self.cliente_id is not None:
            raise ValueError("cliente_id só se aplica a direcao=VENDA")
        return self


class UpdatePriceTableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nome: str | None = None
    vigencia_fim: date | None = None


class CreatePriceTableItemRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    unidade_calculo: PriceTableUnit
    categoria_veiculo_id: uuid.UUID | None = None
    origem_uf: str | None = None
    destino_uf: str | None = None
    faixa_distancia_min_km: Decimal | None = None
    faixa_distancia_max_km: Decimal | None = None
    faixa_modo: FaixaDistanciaMode | None = None
    valor: Decimal
    valor_minimo: Decimal | None = None
    adicional_fixo: Decimal | None = None
    desconto_fixo: Decimal | None = None
    adicional_percentual: Decimal | None = None
    desconto_percentual: Decimal | None = None
    base_percentual_descricao: str | None = None
