from __future__ import annotations

import uuid
from datetime import datetime

from modules.storage.domain.value_objects.file_origin import FileOrigin
from modules.storage.domain.value_objects.file_status import FileStatus
from shared_kernel.domain.base_entity import BaseEntity


class File(BaseEntity[uuid.UUID]):
    """`arquivos` (D315/D324). D415 — nasce `ATIVO` já em `declare()` (chamado por `POST
    /storage/uploads`), já que `arquivos_status_enum` não tem um valor intermediário para "upload
    declarado, binário ainda não confirmado"; `confirm()` (chamado por `commands/complete`) não cria
    a linha, só corrige `tamanho_bytes`/`hash_sha256` com o valor real, lido de volta do Storage."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        nome_original: str,
        tipo_mime: str,
        tamanho_bytes: int,
        hash_sha256: str,
        versao: int,
        arquivo_anterior_id: uuid.UUID | None,
        origem: FileOrigin,
        storage_key: str,
        status: FileStatus,
        criado_em: datetime,
        criado_por: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.nome_original = nome_original
        self.tipo_mime = tipo_mime
        self.tamanho_bytes = tamanho_bytes
        self.hash_sha256 = hash_sha256
        self.versao = versao
        self.arquivo_anterior_id = arquivo_anterior_id
        self.origem = origem
        self.storage_key = storage_key
        self.status = status
        self.criado_em = criado_em
        self.criado_por = criado_por

    @classmethod
    def declare(
        cls,
        *,
        nome_original: str,
        tipo_mime: str,
        tamanho_bytes: int,
        origem: FileOrigin,
        storage_key: str,
        versao: int,
        arquivo_anterior_id: uuid.UUID | None,
        now: datetime,
        created_by: uuid.UUID | None,
    ) -> "File":
        return cls(
            id=uuid.uuid4(),
            nome_original=nome_original,
            tipo_mime=tipo_mime,
            tamanho_bytes=tamanho_bytes,
            hash_sha256="",
            versao=versao,
            arquivo_anterior_id=arquivo_anterior_id,
            origem=origem,
            storage_key=storage_key,
            status=FileStatus.ATIVO,
            criado_em=now,
            criado_por=created_by,
        )

    def confirm(self, *, tamanho_bytes: int, hash_sha256: str) -> None:
        self.tamanho_bytes = tamanho_bytes
        self.hash_sha256 = hash_sha256

    def mark_deleted(self) -> None:
        self.status = FileStatus.EXCLUIDO
