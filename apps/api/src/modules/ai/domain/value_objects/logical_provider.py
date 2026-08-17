from __future__ import annotations

from enum import StrEnum


class LogicalProvider(StrEnum):
    """D170/D309 — nunca o nome do provedor real (OpenAI/Anthropic/Gemini/Azure/Ollama)."""

    INTERNO = "INTERNO"
    PROVEDOR_EXTERNO = "PROVEDOR_EXTERNO"
