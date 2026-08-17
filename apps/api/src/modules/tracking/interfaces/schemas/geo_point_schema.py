from __future__ import annotations

from pydantic import BaseModel


class GeoPointSchema(BaseModel):
    latitude: float
    longitude: float
