from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.ai.application.commands.accept_suggestion import AcceptSuggestionCommand, AcceptSuggestionHandler
from modules.ai.application.commands.ignore_suggestion import IgnoreSuggestionCommand, IgnoreSuggestionHandler
from modules.ai.application.commands.reject_suggestion import RejectSuggestionCommand, RejectSuggestionHandler
from modules.ai.application.queries.get_suggestion import GetSuggestionHandler, GetSuggestionQuery
from modules.ai.application.queries.list_suggestions import ListSuggestionsHandler, ListSuggestionsQuery
from modules.ai.interfaces.schemas.ai_suggestion_schemas import AISuggestionResponse, RejectSuggestionRequest
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ai/suggestions", tags=["AI Suggestions"])


@router.get("")
async def list_suggestions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    target_entity_type: str | None = None,
    target_entity_id: uuid.UUID | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("ai.suggestion.view")),
) -> dict[str, Any]:
    handler = ListSuggestionsHandler(get_session_factory())
    result = await handler.handle(
        ListSuggestionsQuery(
            actor=actor, page=page, limit=limit, category=category, target_entity_type=target_entity_type,
            target_entity_id=target_entity_id, status=status,
        )
    )
    return {
        "data": [AISuggestionResponse.from_dto(s) for s in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{suggestion_id}", response_model=AISuggestionResponse)
async def get_suggestion(
    suggestion_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("ai.suggestion.view"))
) -> AISuggestionResponse:
    handler = GetSuggestionHandler(get_session_factory())
    dto = await handler.handle(GetSuggestionQuery(actor=actor, suggestion_id=suggestion_id))
    return AISuggestionResponse.from_dto(dto)


@router.post("/{suggestion_id}/commands/accept", response_model=AISuggestionResponse)
async def accept_suggestion(
    suggestion_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("ai.suggestion.decide"))
) -> AISuggestionResponse:
    # D311 — só registra a decisão; executar a ação sugerida é sempre uma chamada separada e
    # explícita ao comando do bounded context operacional responsável.
    handler = AcceptSuggestionHandler()
    dto = await handler.handle(AcceptSuggestionCommand(actor=actor, suggestion_id=suggestion_id))
    return AISuggestionResponse.from_dto(dto)


@router.post("/{suggestion_id}/commands/reject", response_model=AISuggestionResponse)
async def reject_suggestion(
    suggestion_id: uuid.UUID, body: RejectSuggestionRequest,
    actor: AuthenticatedActor = Depends(require_permission("ai.suggestion.decide")),
) -> AISuggestionResponse:
    handler = RejectSuggestionHandler()
    dto = await handler.handle(
        RejectSuggestionCommand(actor=actor, suggestion_id=suggestion_id, justification=body.justification)
    )
    return AISuggestionResponse.from_dto(dto)


@router.post("/{suggestion_id}/commands/ignore", response_model=AISuggestionResponse)
async def ignore_suggestion(
    suggestion_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("ai.suggestion.decide"))
) -> AISuggestionResponse:
    handler = IgnoreSuggestionHandler()
    dto = await handler.handle(IgnoreSuggestionCommand(actor=actor, suggestion_id=suggestion_id))
    return AISuggestionResponse.from_dto(dto)
