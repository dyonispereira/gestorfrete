from __future__ import annotations

import uuid
from datetime import date, datetime

from core.exceptions.base import ConflictError, ValidationError
from modules.pricing.domain.value_objects.price_table_direction import PriceTableDirection
from modules.pricing.domain.value_objects.price_table_status import PriceTableStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class PriceTable(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `pricing` — `tabelas_preco`. `direcao=VENDA` aplica a frete cobrado do
    cliente; `direcao=COMPRA` ao frete pago a um transportador (só CRUD nesta fase — "aplicação
    definitiva" de COMPRA numa Viagem fica bloqueada até `carriers`/Transportador existir, Lote 5).

    `versao` (mesmo padrão de `Tenant.versao`) incrementa a cada mutação pós-criação — é isso que
    `TripPriceApplication` (em `freight`) grava no snapshot, para provar exatamente qual versão da
    tabela estava vigente no momento da aplicação, mesmo que só `vigencia_fim`/`status` mudem
    depois (os itens em si já são imutáveis assim que a tabela sai de `RASCUNHO`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        nome: str,
        direcao: PriceTableDirection,
        versao: int,
        vigencia_inicio: date,
        vigencia_fim: date | None,
        cliente_id: uuid.UUID | None,
        status: PriceTableStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.nome = nome
        self.direcao = direcao
        self.versao = versao
        self.vigencia_inicio = vigencia_inicio
        self.vigencia_fim = vigencia_fim
        self.cliente_id = cliente_id
        self.status = status
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        nome: str,
        direcao: PriceTableDirection,
        vigencia_inicio: date,
        vigencia_fim: date | None,
        cliente_id: uuid.UUID | None,
        audit: AuditMetadata,
    ) -> "PriceTable":
        if vigencia_fim is not None and vigencia_fim <= vigencia_inicio:
            raise ValidationError(
                "PRICING_PRICE_TABLE_VIGENCIA_INVALIDA", "vigencia_fim deve ser posterior a vigencia_inicio."
            )
        if direcao == PriceTableDirection.COMPRA and cliente_id is not None:
            raise ValidationError(
                "PRICING_PRICE_TABLE_CLIENTE_SO_VENDA", "cliente_id só se aplica a tabelas de direção VENDA."
            )
        return cls(
            id=uuid.uuid4(),
            nome=nome,
            direcao=direcao,
            versao=1,
            vigencia_inicio=vigencia_inicio,
            vigencia_fim=vigencia_fim,
            cliente_id=cliente_id,
            status=PriceTableStatus.RASCUNHO,
            audit=audit,
        )

    def activate(self, *, updated_by: uuid.UUID, now: datetime) -> None:
        if self.status != PriceTableStatus.RASCUNHO:
            raise ConflictError(
                "PRICING_PRICE_TABLE_INVALID_STATUS", f"Tabela está {self.status.value}, não pode ser ativada."
            )
        self.status = PriceTableStatus.VIGENTE
        self.versao += 1
        self.audit = self.audit.touched(by=updated_by, at=now)

    def expire(self, *, updated_by: uuid.UUID, now: datetime) -> None:
        if self.status != PriceTableStatus.VIGENTE:
            raise ConflictError(
                "PRICING_PRICE_TABLE_INVALID_STATUS", f"Tabela está {self.status.value}, não pode ser expirada."
            )
        self.status = PriceTableStatus.EXPIRADA
        self.versao += 1
        self.audit = self.audit.touched(by=updated_by, at=now)

    def update(
        self, *, nome: str | None, vigencia_fim: date | None, updated_by: uuid.UUID, now: datetime
    ) -> None:
        """Editável em qualquer status não-terminal — `nome` é só rótulo; `vigencia_fim` pode ser
        estendido/reduzido mesmo com a tabela já `VIGENTE` (não reabre os itens, que continuam
        imutáveis). `vigencia_inicio`/`direcao`/`cliente_id` nunca mudam depois de criados — trocar
        qualquer um deles é uma tabela nova."""

        if self.status == PriceTableStatus.EXPIRADA:
            raise ConflictError("PRICING_PRICE_TABLE_INVALID_STATUS", "Tabela EXPIRADA não pode ser editada.")
        if vigencia_fim is not None and vigencia_fim <= self.vigencia_inicio:
            raise ValidationError(
                "PRICING_PRICE_TABLE_VIGENCIA_INVALIDA", "vigencia_fim deve ser posterior a vigencia_inicio."
            )
        if nome is not None:
            self.nome = nome
        if vigencia_fim is not None:
            self.vigencia_fim = vigencia_fim
        self.versao += 1
        self.audit = self.audit.touched(by=updated_by, at=now)
