from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Query

from core.database.session import get_session_factory
from modules.analytics.application.commands.create_snapshot import CreateSnapshotCommand, CreateSnapshotHandler
from modules.analytics.application.queries.get_snapshot import GetSnapshotHandler, GetSnapshotQuery
from modules.analytics.application.queries.list_snapshots import ListSnapshotsHandler, ListSnapshotsQuery
from modules.analytics.interfaces.schemas.analytical_snapshot_schemas import (
    AnalyticalSnapshotResponse,
    CreateSnapshotRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/analytics/snapshots", tags=["Analytical Snapshots"])


@router.get("")
async def list_snapshots(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    reference_period: str | None = None,
    processing_origin: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("analytics.snapshot.view")),
) -> dict[str, Any]:
    handler = ListSnapshotsHandler(get_session_factory())
    result = await handler.handle(
        ListSnapshotsQuery(
            actor=actor, page=page, limit=limit, reference_period=reference_period,
            processing_origin=processing_origin, status=status,
        )
    )
    return {
        "data": [AnalyticalSnapshotResponse.from_dto(s) for s in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{snapshot_id}", response_model=AnalyticalSnapshotResponse)
async def get_snapshot(
    snapshot_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("analytics.snapshot.view"))
) -> AnalyticalSnapshotResponse:
    handler = GetSnapshotHandler(get_session_factory())
    dto = await handler.handle(GetSnapshotQuery(actor=actor, snapshot_id=snapshot_id))
    return AnalyticalSnapshotResponse.from_dto(dto)


@router.post("", response_model=AnalyticalSnapshotResponse, status_code=201)
async def create_snapshot(
    body: CreateSnapshotRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    actor: AuthenticatedActor = Depends(require_permission("analytics.snapshot.create")),
) -> AnalyticalSnapshotResponse:
    # D418 — `Idempotency-Key` aceito/documentado, sem enforcement real (gap pré-existente do
    # projeto inteiro desde o Lote 2, ver DECISIONS.md).
    handler = CreateSnapshotHandler()
    dto = await handler.handle(CreateSnapshotCommand(actor=actor, reference_period=body.reference_period))
    return AnalyticalSnapshotResponse.from_dto(dto)
