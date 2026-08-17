from __future__ import annotations

import uuid

from core.exceptions.base import ValidationError
from modules.tracking.domain.value_objects.geo_point import GeoPoint
from modules.tracking.domain.value_objects.geofence_geometry_type import GeofenceGeometryType
from modules.tracking.domain.value_objects.geofence_status import GeofenceStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Geofence(BaseAggregateRoot[uuid.UUID]):
    """`cercas_eletronicas` — configuração (D122/D289), não histórico. CRUD completo, diferente das
    demais entidades deste módulo."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        nome: str,
        tipo_geometria: GeofenceGeometryType,
        centro: GeoPoint | None,
        raio_metros: float | None,
        poligono: list[GeoPoint] | None,
        cliente_id: uuid.UUID | None,
        filial_id: uuid.UUID | None,
        status: GeofenceStatus,
    ) -> None:
        super().__init__(id)
        self.nome = nome
        self.tipo_geometria = tipo_geometria
        self.centro = centro
        self.raio_metros = raio_metros
        self.poligono = poligono
        self.cliente_id = cliente_id
        self.filial_id = filial_id
        self.status = status

    @staticmethod
    def _closed_ring(pontos: list[GeoPoint]) -> list[GeoPoint]:
        if len(pontos) < 3:
            raise ValidationError(
                "TRACKING_GEOFENCE_INVALID_GEOMETRY", "Polígono precisa de ao menos 3 pontos."
            )
        if pontos[0] != pontos[-1]:
            return [*pontos, pontos[0]]
        return pontos

    @classmethod
    def create(
        cls,
        *,
        nome: str,
        tipo_geometria: GeofenceGeometryType,
        centro: GeoPoint | None,
        raio_metros: float | None,
        poligono: list[GeoPoint] | None,
        cliente_id: uuid.UUID | None,
        filial_id: uuid.UUID | None,
    ) -> "Geofence":
        cls._validate_geometry(tipo_geometria, centro, raio_metros, poligono)
        fechado = cls._closed_ring(poligono) if tipo_geometria == GeofenceGeometryType.POLIGONO and poligono else None
        return cls(
            id=uuid.uuid4(), nome=nome, tipo_geometria=tipo_geometria, centro=centro,
            raio_metros=raio_metros, poligono=fechado, cliente_id=cliente_id, filial_id=filial_id,
            status=GeofenceStatus.ATIVA,
        )

    @staticmethod
    def _validate_geometry(
        tipo_geometria: GeofenceGeometryType, centro: GeoPoint | None, raio_metros: float | None,
        poligono: list[GeoPoint] | None,
    ) -> None:
        if tipo_geometria == GeofenceGeometryType.CIRCULO:
            if centro is None or raio_metros is None or raio_metros <= 0:
                raise ValidationError(
                    "TRACKING_GEOFENCE_INVALID_GEOMETRY",
                    "Geofence CIRCULO exige centro e raio_metros maior que zero.",
                )
        elif tipo_geometria == GeofenceGeometryType.POLIGONO:
            if not poligono or len(poligono) < 3:
                raise ValidationError(
                    "TRACKING_GEOFENCE_INVALID_GEOMETRY", "Geofence POLIGONO exige ao menos 3 pontos."
                )

    def update(
        self,
        *,
        nome: str | None,
        tipo_geometria: GeofenceGeometryType | None,
        centro: GeoPoint | None,
        raio_metros: float | None,
        poligono: list[GeoPoint] | None,
        cliente_id: uuid.UUID | None,
        filial_id: uuid.UUID | None,
        status: GeofenceStatus | None,
    ) -> None:
        if nome is not None:
            self.nome = nome
        if tipo_geometria is not None:
            self._validate_geometry(tipo_geometria, centro, raio_metros, poligono)
            self.tipo_geometria = tipo_geometria
            self.centro = centro
            self.raio_metros = raio_metros
            self.poligono = self._closed_ring(poligono) if tipo_geometria == GeofenceGeometryType.POLIGONO and poligono else None
        if cliente_id is not None:
            self.cliente_id = cliente_id
        if filial_id is not None:
            self.filial_id = filial_id
        if status is not None:
            self.status = status
