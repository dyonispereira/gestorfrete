from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from modules.ai.domain.entities.ai_model import AIModel


@dataclass(frozen=True)
class AIModelGatewayResult:
    output: dict[str, Any]
    confidence_level: Decimal
    cost: Decimal | None


class AIModelGateway(ABC):
    """D170/D423 — port. O domínio conhece apenas `AIModel` (identidade lógica); esta interface é a
    única fronteira entre `ai` e "executar um modelo de verdade". Nenhuma implementação real de
    provedor (OpenAI/Anthropic/Gemini/Azure/Ollama) existe nesta fundação — só
    `FakeAIModelGateway` (`infrastructure/gateways`), determinística. Integração real fica para uma
    futura sprint de integrações; trocar o adapter então não toca `domain`/`application`."""

    @abstractmethod
    async def run(self, *, model: AIModel, input: dict[str, Any]) -> AIModelGatewayResult: ...
