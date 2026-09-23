from __future__ import annotations

from enum import StrEnum


class OdometerOrigin(StrEnum):
    ABASTECIMENTO = "ABASTECIMENTO"
    CHECKLIST = "CHECKLIST"
    MANUAL = "MANUAL"
    TELEMETRIA = "TELEMETRIA"
    ORDEM_SERVICO = "ORDEM_SERVICO"
    # V1 Operational Hardening, Parte 2 — leituras de fronteira de uma Viagem (KM_INICIAL/KM_FINAL,
    # `003-frota.md`), capturadas por `freight` no despacho/encerramento via `TripOdometerRecorder`.
    DESPACHO_VIAGEM = "DESPACHO_VIAGEM"
    ENCERRAMENTO_VIAGEM = "ENCERRAMENTO_VIAGEM"
