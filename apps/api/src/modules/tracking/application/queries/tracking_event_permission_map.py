from __future__ import annotations

from modules.tracking.domain.value_objects.tracking_event_type import TrackingEventType

# D294 — `eventos_rastreamento` é uma única tabela, mas a autorização é fragmentada por categoria de
# `tipo` (`051-tracking-events.md`). `ENTROU_GEOFENCE`/`SAIU_GEOFENCE` e `IGNICAO_LIGADA`/
# `IGNICAO_DESLIGADA` reaproveitam código já existente (geofence/posição) — nenhum código novo de
# RBAC foi criado para essas duas categorias.
EVENT_TYPE_PERMISSION: dict[TrackingEventType, str] = {
    TrackingEventType.PARADA_DETECTADA: "tracking.stop.view",
    TrackingEventType.DESVIO_DE_ROTA_DETECTADO: "tracking.route_deviation.view",
    TrackingEventType.EXCESSO_DE_VELOCIDADE: "tracking.speed_event.view",
    TrackingEventType.ENTROU_GEOFENCE: "tracking.geofence.view",
    TrackingEventType.SAIU_GEOFENCE: "tracking.geofence.view",
    TrackingEventType.IGNICAO_LIGADA: "tracking.position.view",
    TrackingEventType.IGNICAO_DESLIGADA: "tracking.position.view",
}
