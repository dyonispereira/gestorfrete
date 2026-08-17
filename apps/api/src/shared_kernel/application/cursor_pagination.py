from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime


def encode_cursor(*, data_hora: datetime, id: uuid.UUID) -> str:
    """Cursor opaco (`PAGINATION.md`) — Base64 de `{coluna_de_ordenação, id}` da última linha da
    página anterior. Extraído para `shared_kernel` a partir do segundo/terceiro/quarto/quinto
    consumidor real (`odometer_reading`, Lote 4; `cte`/`mdfe`/`ciot` status-history + `fiscal_event`,
    Lote 7) — não extraído antes por falta de necessidade real (D076-like disciplina)."""

    payload = {"data_hora": data_hora.isoformat(), "id": str(id)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Levanta `ValueError` genérico em vez de `core.exceptions.base.ValidationError` — Shared
    Kernel nunca importa `core` (contrato `import-linter` "Shared Kernel never imports core,
    modules or interfaces"). Cada chamador (Application layer de um módulo) converte para o próprio
    código de erro de domínio."""

    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return datetime.fromisoformat(payload["data_hora"]), uuid.UUID(payload["id"])
    except Exception as exc:
        raise ValueError("Cursor de paginação inválido.") from exc
