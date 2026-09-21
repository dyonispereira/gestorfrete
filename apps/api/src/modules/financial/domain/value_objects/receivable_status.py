from __future__ import annotations

from enum import StrEnum


class ReceivableStatus(StrEnum):
    PENDENTE = "PENDENTE"
    VENCIDA = "VENCIDA"
    # Reconciliado (Lote Financeiro, Parte 2.1) — baixa parcial real de uma parcela isolada.
    # `docs/domain/006-financeiro.md`/`docs/flows/005-FINANCEIRO.md` nunca modelaram esse estado;
    # o design anterior tratava "parcelamento" (N Contas a Receber por Fatura) como o único
    # mecanismo de recebimento parcial. Ver nota de reconciliação nesses dois documentos.
    PARCIALMENTE_RECEBIDO = "PARCIALMENTE_RECEBIDO"
    RECEBIDA = "RECEBIDA"
    CONCILIADA = "CONCILIADA"
