from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.config.settings import get_settings
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.storage.application.dtos.file_dto import FileDTO
from modules.storage.infrastructure.object_storage import (
    compute_object_hash,
    delete_object,
    stat_object,
)
from modules.storage.infrastructure.persistence.repositories.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CompleteFileUploadCommand(Command):
    actor: AuthenticatedActor
    file_id: uuid.UUID


class CompleteFileUploadHandler(CommandHandler[CompleteFileUploadCommand, FileDTO]):
    """Production Readiness Hardening, Parte 3 — a validação em `UploadFileHandler` confia no
    `size_bytes` declarado pelo cliente; aqui é onde o tamanho REAL, devolvido pelo próprio MinIO
    via `stat_object`, é conferido contra o mesmo teto. Um upload que excede o limite é rejeitado e
    o objeto físico é apagado do Storage — nunca fica ocupando espaço indefinidamente só porque o
    cliente mentiu no `size_bytes` declarado na Parte 1 da validação."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CompleteFileUploadCommand) -> FileDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            file_repo = SqlAlchemyFileRepository(uow.session)
            file = await file_repo.get_by_id(command.file_id)
            if file is None:
                raise NotFoundError("STORAGE_FILE_NOT_FOUND", "Arquivo não encontrado.")

            size_bytes = await stat_object(file.storage_key)
            if size_bytes is None:
                raise ConflictError(
                    "STORAGE_UPLOAD_NOT_FOUND_IN_PROVIDER", "Binário ainda não chegou ao Storage."
                )

            max_size = get_settings().upload_max_size_bytes
            if size_bytes > max_size:
                await delete_object(file.storage_key)
                file.mark_deleted()
                await file_repo.add(file)
                await self._audit.record(
                    uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="arquivos", entidade_id=file.id,
                    acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id,
                    ator_nome_snapshot=str(command.actor.user_id),
                    motivo=f"Upload rejeitado: {size_bytes} bytes excede o limite de {max_size} bytes.",
                )
                await uow.commit()
                raise ConflictError(
                    "STORAGE_UPLOAD_SIZE_EXCEEDS_LIMIT",
                    f"O arquivo enviado ({size_bytes} bytes) excede o tamanho máximo permitido "
                    f"({max_size} bytes). O upload foi rejeitado e removido do Storage.",
                )

            hash_sha256 = await compute_object_hash(file.storage_key)

            file.confirm(tamanho_bytes=size_bytes, hash_sha256=hash_sha256)
            await file_repo.add(file)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="arquivos", entidade_id=file.id,
                acao="ALTERACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"hash": hash_sha256, "size_bytes": size_bytes},
            )
            await uow.commit()

        return FileDTO.from_entity(file)
