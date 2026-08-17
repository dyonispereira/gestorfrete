from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from modules.tracking.domain.entities.geofence import Geofence
from modules.tracking.domain.value_objects.geo_point import GeoPoint


class GeofenceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Geofence | None: ...

    @abstractmethod
    async def get_by_nome(self, nome: str) -> Geofence | None: ...

    @abstractmethod
    async def list_active_ids_containing(self, point: GeoPoint) -> list[uuid.UUID]:
        """Contenção calculada inteiramente em SQL (`ST_DWithin`/`ST_Covers`), nunca em Python —
        usado por `TrackingIngestion` a cada Posição nova (`052-geofences.md`). Empurrar a conta
        para o Postgres é o que permite o índice `GIST` (D197) ser de fato usado (Auditoria #3)."""
        ...

    @abstractmethod
    async def list_page(
        self, *, page: int, limit: int, search: str | None, geometry_type: str | None,
        client_id: uuid.UUID | None, branch_id: uuid.UUID | None, status: str | None,
    ) -> tuple[list[Geofence], int]: ...

    @abstractmethod
    async def add(self, geofence: Geofence) -> None: ...

    @abstractmethod
    async def is_referenced_by_recent_events(self, id: uuid.UUID) -> bool:
        """`TRACKING_GEOFENCE_IN_USE` (422) — `eventos_rastreamento.cerca_eletronica_id` histórico
        nunca é apagado (D001), mas a exclusão pode exigir confirmação quando há eventos recentes."""
        ...

    @abstractmethod
    async def delete(self, geofence: Geofence) -> None:
        """Soft delete (D219) — implementado como `status = INATIVA`, nunca `DELETE FROM`."""
        ...
