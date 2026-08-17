from __future__ import annotations

from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.analytics.application.dtos.analytical_snapshot_dto import AnalyticalSnapshotDTO
from modules.analytics.domain.entities.analytical_snapshot import AnalyticalSnapshot
from modules.analytics.domain.value_objects.snapshot_processing_origin import SnapshotProcessingOrigin
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytical_snapshot_repository import (
    SqlAlchemyAnalyticalSnapshotRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateSnapshotCommand(Command):
    actor: AuthenticatedActor
    reference_period: str


class CreateSnapshotHandler(CommandHandler[CreateSnapshotCommand, AnalyticalSnapshotDTO]):
    """`064` — só inicia a consolidação (`EM_PROCESSAMENTO`); `origin` sempre `MANUAL` aqui
    (`AUTOMATICO` reservado a `Agendamento de Atualização`, D159). A consolidação em si é
    `AnalyticsCalculationEngine.consolidate_snapshot` (D420), fora deste Handler."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateSnapshotCommand) -> AnalyticalSnapshotDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAnalyticalSnapshotRepository(uow.session)

            if await repo.get_consolidated_for_period(command.reference_period) is not None:
                raise ConflictError(
                    "ANALYTICS_SNAPSHOT_PERIOD_ALREADY_CONSOLIDATED",
                    "Já existe um Snapshot consolidado para este período.",
                )

            snapshot = AnalyticalSnapshot.start(
                tenant_id=command.actor.tenant_id, periodo_referencia=command.reference_period,
                origem_processamento=SnapshotProcessingOrigin.MANUAL, usuario_id=command.actor.user_id,
            )
            await repo.add(snapshot)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="snapshots_analiticos",
                entidade_id=snapshot.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"reference_period": command.reference_period},
            )
            await uow.commit()

        return AnalyticalSnapshotDTO.from_entity(snapshot, participating_metrics=[], indicator_ids=[])
