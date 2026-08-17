from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoPoint:
    """Coordenada WGS 84 (SRID 4326) — nunca WKT/PostGIS bruto exposto fora da camada de
    infraestrutura (`components/tracking-schemas.md#/GeoPoint`)."""

    latitude: float
    longitude: float
