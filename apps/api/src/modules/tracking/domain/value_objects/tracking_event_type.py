from __future__ import annotations

from enum import StrEnum


class TrackingEventType(StrEnum):
    """Consolidação D076 — sete categorias (`relational/008-rastreamento.md`). `PARADA_DETECTADA`/
    `DESVIO_DE_ROTA_DETECTADO` não têm gatilho automático nesta lote (D402) — o valor existe no
    Enum físico e na API, só sem algoritmo de detecção ainda."""

    PARADA_DETECTADA = "PARADA_DETECTADA"
    DESVIO_DE_ROTA_DETECTADO = "DESVIO_DE_ROTA_DETECTADO"
    EXCESSO_DE_VELOCIDADE = "EXCESSO_DE_VELOCIDADE"
    ENTROU_GEOFENCE = "ENTROU_GEOFENCE"
    SAIU_GEOFENCE = "SAIU_GEOFENCE"
    IGNICAO_LIGADA = "IGNICAO_LIGADA"
    IGNICAO_DESLIGADA = "IGNICAO_DESLIGADA"
