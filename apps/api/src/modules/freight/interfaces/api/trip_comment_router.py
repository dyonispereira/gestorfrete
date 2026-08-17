from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.freight.application.commands.create_trip_comment import CreateTripCommentCommand, CreateTripCommentHandler
from modules.freight.application.commands.delete_trip_comment import DeleteTripCommentCommand, DeleteTripCommentHandler
from modules.freight.application.commands.update_trip_comment import UpdateTripCommentCommand, UpdateTripCommentHandler
from modules.freight.application.queries.list_trip_comments import ListTripCommentsHandler, ListTripCommentsQuery
from modules.freight.interfaces.schemas.comment_schemas import (
    CommentResponse,
    CreateCommentRequest,
    UpdateCommentRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Comments"])


@router.get("/{trip_id}/comments")
async def list_trip_comments(
    trip_id: uuid.UUID,
    visible_to_client: bool | None = Query(default=None),
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.view")),
) -> dict[str, Any]:
    handler = ListTripCommentsHandler(get_session_factory())
    items = await handler.handle(
        ListTripCommentsQuery(actor=actor, trip_id=trip_id, visible_to_client=visible_to_client)
    )
    responses = [CommentResponse.from_entity(c) for c in items]
    return {"data": responses, "meta": {"pagination": {"page": 1, "limit": len(responses), "total": len(responses)}}}


@router.post("/{trip_id}/comments", response_model=CommentResponse, status_code=201)
async def create_trip_comment(
    trip_id: uuid.UUID, body: CreateCommentRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.trip.view")),
) -> CommentResponse:
    handler = CreateTripCommentHandler()
    comment = await handler.handle(
        CreateTripCommentCommand(actor=actor, trip_id=trip_id, text=body.text, visible_to_client=body.visible_to_client)
    )
    return CommentResponse.from_entity(comment)


@router.patch("/{trip_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_trip_comment(
    trip_id: uuid.UUID, comment_id: uuid.UUID, body: UpdateCommentRequest,
    actor: AuthenticatedActor = Depends(require_permission("storage.comment.edit_own")),
) -> CommentResponse:
    handler = UpdateTripCommentHandler()
    comment = await handler.handle(
        UpdateTripCommentCommand(
            actor=actor, trip_id=trip_id, comment_id=comment_id, text=body.text,
            visible_to_client=body.visible_to_client,
        )
    )
    return CommentResponse.from_entity(comment)


@router.delete("/{trip_id}/comments/{comment_id}", status_code=204, response_model=None)
async def delete_trip_comment(
    trip_id: uuid.UUID, comment_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("storage.comment.delete_own")),
) -> None:
    handler = DeleteTripCommentHandler()
    await handler.handle(DeleteTripCommentCommand(actor=actor, trip_id=trip_id, comment_id=comment_id))
