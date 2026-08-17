from __future__ import annotations

from core.database.session import get_session_factory
from core.security.session_validation import set_session_validator
from modules.identity_access.infrastructure.session_validator_adapter import SqlAlchemySessionValidator


def register() -> None:
    """Chamado uma vez por `main.py` no composition root — conecta a Foundation (Lote 1) ao
    primeiro bounded context real: `get_current_actor` (`core`) passa a validar sessões de verdade
    em vez do `_NullSessionValidator` default."""

    set_session_validator(SqlAlchemySessionValidator(get_session_factory()))
