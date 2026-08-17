from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.tracking.domain.entities.location_origin import LocationOrigin
from modules.tracking.domain.repositories.location_origin_repository import LocationOriginRepository
from modules.tracking.infrastructure.persistence.models.location_origin_model import LocationOriginModel


def _to_entity(model: LocationOriginModel) -> LocationOrigin:
    return LocationOrigin(id=model.id, nome=model.nome, precisao_tipica_metros=model.precisao_tipica_metros)


class SqlAlchemyLocationOriginRepository(LocationOriginRepository):
    """Platform Reference Data (D046) — sem `tenant_id`, nenhum filtro de tenant nas consultas."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> LocationOrigin | None:
        model = (
            await self._session.execute(select(LocationOriginModel).where(LocationOriginModel.id == id))
        ).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_nome(self, nome: str) -> LocationOrigin | None:
        model = (
            await self._session.execute(select(LocationOriginModel).where(LocationOriginModel.nome == nome))
        ).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(self, *, page: int, limit: int) -> tuple[list[LocationOrigin], int]:
        count_stmt = select(func.count()).select_from(LocationOriginModel)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = select(LocationOriginModel).order_by(LocationOriginModel.nome.asc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, origin: LocationOrigin) -> None:
        # D406 — idempotente via `ON CONFLICT (nome) DO NOTHING`, mesmo mecanismo de `SEED_DATA.md`
        # §6 usado pelo seed de teste/bootstrap (`_seed_location_origins`).
        stmt = pg_insert(LocationOriginModel).values(
            id=origin.id, nome=origin.nome, precisao_tipica_metros=origin.precisao_tipica_metros,
        ).on_conflict_do_nothing(index_elements=["nome"])
        await self._session.execute(stmt)
        await self._session.flush()
