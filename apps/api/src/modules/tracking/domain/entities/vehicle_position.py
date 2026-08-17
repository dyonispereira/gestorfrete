from __future__ import annotations

import uuid
from datetime import datetime

from modules.tracking.domain.value_objects.geo_point import GeoPoint
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class VehiclePosition(BaseAggregateRoot[uuid.UUID]):
    """`posicoes_veiculo` — Time Series (D191), imutável desde a concepção (D121): nasce pronta, de
    uma única fonte (o Equipamento), e nunca é tocada de novo. Toda linha nova é um `INSERT`, nunca
    um `UPDATE` — não existe método de mutação nesta classe além do construtor/`create`."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        veiculo_tracionador_id: uuid.UUID,
        equipamento_rastreamento_id: uuid.UUID,
        localizacao: GeoPoint,
        origem_localizacao_id: uuid.UUID,
        precisao_metros: float | None,
        numero_satelites: int | None,
        hdop: float | None,
        nivel_confianca: float | None,
        capturado_em: datetime,
        recebido_em: datetime,
        processado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.equipamento_rastreamento_id = equipamento_rastreamento_id
        self.localizacao = localizacao
        self.origem_localizacao_id = origem_localizacao_id
        self.precisao_metros = precisao_metros
        self.numero_satelites = numero_satelites
        self.hdop = hdop
        self.nivel_confianca = nivel_confianca
        self.capturado_em = capturado_em
        self.recebido_em = recebido_em
        self.processado_em = processado_em

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        equipamento_rastreamento_id: uuid.UUID,
        localizacao: GeoPoint,
        origem_localizacao_id: uuid.UUID,
        precisao_metros: float | None = None,
        numero_satelites: int | None = None,
        hdop: float | None = None,
        nivel_confianca: float | None = None,
        capturado_em: datetime,
        recebido_em: datetime,
        processado_em: datetime,
    ) -> "VehiclePosition":
        return cls(
            id=uuid.uuid4(), veiculo_tracionador_id=veiculo_tracionador_id,
            equipamento_rastreamento_id=equipamento_rastreamento_id, localizacao=localizacao,
            origem_localizacao_id=origem_localizacao_id, precisao_metros=precisao_metros,
            numero_satelites=numero_satelites, hdop=hdop, nivel_confianca=nivel_confianca,
            capturado_em=capturado_em, recebido_em=recebido_em, processado_em=processado_em,
        )
