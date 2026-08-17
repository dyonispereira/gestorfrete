from __future__ import annotations

from enum import StrEnum


class UserStatus(StrEnum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    BLOQUEADO = "BLOQUEADO"


class SessionStatus(StrEnum):
    ATIVA = "ATIVA"
    EXPIRADA = "EXPIRADA"
    ENCERRADA = "ENCERRADA"


class SessionEndedReason(StrEnum):
    LOGOUT = "Logout"
    REVOGACAO_ADMINISTRATIVA = "RevogacaoAdministrativa"
    PASSWORD_RESET = "PasswordReset"
