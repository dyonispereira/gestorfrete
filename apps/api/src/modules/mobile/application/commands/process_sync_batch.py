from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.session import get_session_factory
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ApplicationError, ConflictError, ValidationError
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.identity_access.application.authorization_service import AuthorizationService
from modules.mobile.application.dtos.sync_dto import SyncBatchResultDTO, SyncItemResultDTO
from modules.mobile.application.sync_command_registry import SYNC_COMMAND_HANDLERS
from modules.mobile.domain.entities.sync_queue_item import SyncQueueItem
from modules.mobile.domain.entities.sync_record import SyncRecord
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_sync_queue_item_repository import (
    SqlAlchemySyncQueueItemRepository,
)
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_sync_record_repository import (
    SqlAlchemySyncRecordRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class SyncCommandInput:
    local_id: str
    sequence: int
    command: str
    target_entity_type: str
    target_entity_id: uuid.UUID
    payload: dict[str, Any]


@dataclass(frozen=True)
class ProcessSyncBatchCommand(Command):
    actor: AuthenticatedActor
    session_id: uuid.UUID
    commands: list[SyncCommandInput]


class ProcessSyncBatchHandler(CommandHandler[ProcessSyncBatchCommand, SyncBatchResultDTO]):
    """D410/D298 — despacha cada item para a mesma Application Service do endpoint direto
    equivalente, processando por `sequencia_local` (nunca pela ordem de chegada desta chamada, e
    incluindo itens `PENDENTE`/`FALHOU` de chamadas anteriores da mesma Sessão)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._authz = AuthorizationService(get_session_factory())

    async def handle(self, command: ProcessSyncBatchCommand) -> SyncBatchResultDTO:
        started_at = datetime.now(timezone.utc)

        # 1) Persiste cada item novo — D111, idempotente via `add_if_absent` (INSERT ... ON CONFLICT
        # DO NOTHING); reenviar o mesmo `local_id` nunca cria uma segunda linha.
        async with SQLAlchemyUnitOfWork() as uow:
            queue_repo = SqlAlchemySyncQueueItemRepository(uow.session)
            for item_input in command.commands:
                if item_input.command not in SYNC_COMMAND_HANDLERS:
                    raise ValidationError(
                        "MOBILE_SYNC_UNKNOWN_COMMAND", f"tipo_comando desconhecido: {item_input.command}"
                    )
                await queue_repo.add_if_absent(
                    SyncQueueItem.enqueue(
                        sessao_mobile_id=command.session_id, sequencia_local=item_input.sequence,
                        tipo_comando=item_input.command, entidade_destino_tipo=item_input.target_entity_type,
                        entidade_destino_id=item_input.target_entity_id, payload=item_input.payload,
                        identificador_local_unico=item_input.local_id, now=started_at,
                    )
                )
            await uow.commit()

        # 2) D136/D298 — todos os PENDENTE/FALHOU da Sessão, ordenados por sequencia_local.
        async with SQLAlchemyUnitOfWork() as uow:
            queue_repo = SqlAlchemySyncQueueItemRepository(uow.session)
            pending_items = await queue_repo.list_pending_ordered(command.session_id)

        granted_codes = await self._authz.get_permission_codes(command.actor)

        results: list[SyncItemResultDTO] = []
        success_count = 0
        failure_count = 0

        for item in pending_items:
            spec = SYNC_COMMAND_HANDLERS[item.tipo_comando]

            async with SQLAlchemyUnitOfWork() as uow:
                queue_repo = SqlAlchemySyncQueueItemRepository(uow.session)
                item.mark_processing()
                await queue_repo.update(item)
                await uow.commit()

            missing_codes = [c for c in spec.permission_codes if c not in granted_codes]
            if missing_codes:
                async with SQLAlchemyUnitOfWork() as uow:
                    queue_repo = SqlAlchemySyncQueueItemRepository(uow.session)
                    item.mark_failed()
                    await queue_repo.update(item)
                    await uow.commit()
                results.append(
                    SyncItemResultDTO(
                        local_id=item.identificador_local_unico, result="REJEITADO",
                        error_code="IDENTITY_PERMISSION_DENIED",
                        error_message=f"Ação requer a permissão '{missing_codes[0]}'.",
                    )
                )
                failure_count += 1
                continue

            try:
                result_obj = await spec.execute(command.actor, item.entidade_destino_id, item.payload)
                async with SQLAlchemyUnitOfWork() as uow:
                    queue_repo = SqlAlchemySyncQueueItemRepository(uow.session)
                    item.mark_processed()
                    await queue_repo.update(item)
                    await uow.commit()
                results.append(
                    SyncItemResultDTO(local_id=item.identificador_local_unico, result="PROCESSADO", server_id=result_obj.id)
                )
                success_count += 1
            except ConflictError as exc:
                current_state = await self._fetch_current_state(item)
                async with SQLAlchemyUnitOfWork() as uow:
                    queue_repo = SqlAlchemySyncQueueItemRepository(uow.session)
                    item.mark_conflict(exc.message)
                    await queue_repo.update(item)
                    await uow.commit()
                results.append(
                    SyncItemResultDTO(
                        local_id=item.identificador_local_unico, result="CONFLITO",
                        conflict_current_state=current_state, conflict_reason=exc.message,
                    )
                )
                failure_count += 1
            except ApplicationError as exc:
                async with SQLAlchemyUnitOfWork() as uow:
                    queue_repo = SqlAlchemySyncQueueItemRepository(uow.session)
                    item.mark_failed()
                    await queue_repo.update(item)
                    await uow.commit()
                results.append(
                    SyncItemResultDTO(
                        local_id=item.identificador_local_unico, result="REJEITADO", error_code=exc.code,
                        error_message=exc.message,
                    )
                )
                failure_count += 1

        finished_at = datetime.now(timezone.utc)
        async with SQLAlchemyUnitOfWork() as uow:
            record_repo = SqlAlchemySyncRecordRepository(uow.session)
            record = SyncRecord.create(
                sessao_mobile_id=command.session_id, started_at=started_at, finished_at=finished_at,
                command_count=len(pending_items), success_count=success_count, failure_count=failure_count,
            )
            await record_repo.add(record)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="registros_sincronizacao",
                entidade_id=record.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return SyncBatchResultDTO(sync_record_id=record.id, results=results)

    async def _fetch_current_state(self, item: SyncQueueItem) -> dict[str, Any] | None:
        if item.entidade_destino_tipo != "trip":
            return None
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            trip = await trip_repo.get_by_id(item.entidade_destino_id)
        if trip is None:
            return None
        return {"status_operacional": trip.status_operacional.value}
