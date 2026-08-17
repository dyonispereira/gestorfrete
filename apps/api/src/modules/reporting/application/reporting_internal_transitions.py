from __future__ import annotations

import uuid

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_export_repository import (
    SqlAlchemyExportRepository,
)


class ReportingInternalTransitions:
    """Mesmo espírito de `TripInternalTransitions`/`AnalyticsCalculationEngine` — nunca alcançável
    por HTTP. `069-exports.md` é assíncrona por padrão (D307); nenhum motor real de geração de PDF/
    Excel/CSV existe nesta fundação — estas duas chamadas simulam o worker que processaria a
    Exportação de verdade."""

    async def complete_export(self, *, export_id: uuid.UUID, file_id: uuid.UUID) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyExportRepository(uow.session)
            export = await repo.get_by_id(export_id)
            if export is None:
                raise NotFoundError("REPORTING_EXPORT_NOT_FOUND", "Exportação não encontrada.")
            export.complete(arquivo_id=file_id)
            await repo.add(export)
            await uow.commit()

    async def fail_export(self, *, export_id: uuid.UUID, error_message: str) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyExportRepository(uow.session)
            export = await repo.get_by_id(export_id)
            if export is None:
                raise NotFoundError("REPORTING_EXPORT_NOT_FOUND", "Exportação não encontrada.")
            export.fail(error_message=error_message)
            await repo.add(export)
            await uow.commit()
