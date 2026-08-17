from __future__ import annotations

from enum import StrEnum


class FileOrigin(StrEnum):
    UPLOAD_DIRETO = "UPLOAD_DIRETO"
    GERADO_PELO_SISTEMA = "GERADO_PELO_SISTEMA"
    IMPORTADO = "IMPORTADO"
