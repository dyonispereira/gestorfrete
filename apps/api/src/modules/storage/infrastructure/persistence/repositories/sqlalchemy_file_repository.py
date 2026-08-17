from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.storage.domain.entities.file import File
from modules.storage.domain.repositories.file_repository import FileRepository
from modules.storage.domain.value_objects.file_origin import FileOrigin
from modules.storage.domain.value_objects.file_status import FileStatus
from modules.storage.infrastructure.persistence.models.file_model import FileModel


def _to_entity(model: FileModel) -> File:
    return File(
        id=model.id,
        nome_original=model.nome_original,
        tipo_mime=model.tipo_mime,
        tamanho_bytes=model.tamanho_bytes,
        hash_sha256=model.hash_sha256,
        versao=model.versao,
        arquivo_anterior_id=model.arquivo_anterior_id,
        origem=FileOrigin(model.origem),
        storage_key=model.storage_key,
        status=FileStatus(model.status),
        criado_em=model.criado_em,
        criado_por=model.criado_por,
    )


class SqlAlchemyFileRepository(FileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> File | None:
        tenant_id = get_current_tenant_id()
        stmt = select(FileModel).where(FileModel.id == id, FileModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, mime_type: str | None, origin: str | None, status: str
    ) -> tuple[list[File], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(FileModel).where(FileModel.tenant_id == tenant_id, FileModel.status == status)
        if mime_type is not None:
            stmt = stmt.where(FileModel.tipo_mime == mime_type)
        if origin is not None:
            stmt = stmt.where(FileModel.origem == origin)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(FileModel.criado_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def list_versions(self, file_id: uuid.UUID) -> list[File]:
        """Navega a cadeia inteira (D324) do mais recente ao original, não importa qual `file_id` da
        cadeia foi informado — `arquivo_anterior_id` só aponta para trás, então primeiro anda para a
        frente até achar a versão mais recente (nenhum `arquivo_anterior_id` aponta para ela)."""

        tenant_id = get_current_tenant_id()

        head_id = file_id
        while True:
            newer_stmt = select(FileModel.id).where(
                FileModel.arquivo_anterior_id == head_id, FileModel.tenant_id == tenant_id
            )
            newer_id = (await self._session.execute(newer_stmt)).scalar_one_or_none()
            if newer_id is None:
                break
            head_id = newer_id

        chain: list[File] = []
        current_id: uuid.UUID | None = head_id
        while current_id is not None:
            stmt = select(FileModel).where(FileModel.id == current_id, FileModel.tenant_id == tenant_id)
            model = (await self._session.execute(stmt)).scalar_one_or_none()
            if model is None:
                break
            chain.append(_to_entity(model))
            current_id = model.arquivo_anterior_id
        return chain

    async def add(self, file: File) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(FileModel, file.id)
        if model is None:
            model = FileModel(id=file.id, tenant_id=tenant_id)
            self._session.add(model)
        model.nome_original = file.nome_original
        model.tipo_mime = file.tipo_mime
        model.tamanho_bytes = file.tamanho_bytes
        model.hash_sha256 = file.hash_sha256
        model.versao = file.versao
        model.arquivo_anterior_id = file.arquivo_anterior_id
        model.origem = file.origem.value
        model.storage_key = file.storage_key
        model.status = file.status.value
        model.criado_em = file.criado_em
        model.criado_por = file.criado_por
        await self._session.flush()
