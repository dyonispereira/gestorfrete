from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from modules.ai.domain.entities.ai_model import AIModel
from modules.ai.domain.gateways.ai_model_gateway import AIModelGateway, AIModelGatewayResult
from modules.ai.domain.value_objects.logical_provider import LogicalProvider


class FakeAIModelGateway(AIModelGateway):
    """D170/D423 — única implementação de `AIModelGateway` nesta fundação. Determinística: o mesmo
    `input` sempre produz o mesmo `output`/`confidence_level` (hash SHA-256 do `input` serializado,
    sem chamada de rede, sem SDK de provedor real). `cost` só é preenchido para
    `fornecedor_logico=PROVEDOR_EXTERNO` — um modelo interno nunca tem custo variável."""

    async def run(self, *, model: AIModel, input: dict[str, Any]) -> AIModelGatewayResult:
        digest = hashlib.sha256(json.dumps(input, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        confidence_level = Decimal(int(digest[:4], 16) % 4001) / Decimal(100) + Decimal("60.00")
        output = {"digest": digest, "model": model.nome, "summary": f"resultado determinístico para {digest[:8]}"}
        cost = Decimal("0.0125") if model.fornecedor_logico == LogicalProvider.PROVEDOR_EXTERNO else None
        return AIModelGatewayResult(output=output, confidence_level=confidence_level, cost=cost)
