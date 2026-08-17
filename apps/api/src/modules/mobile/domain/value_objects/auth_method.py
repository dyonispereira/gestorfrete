from __future__ import annotations

from enum import StrEnum


class AuthMethod(StrEnum):
    """Vocabulário extensível (mesmo princípio de D120) — hoje só `CPF_VEICULO` é validado de
    verdade (D409); `BIOMETRIA`/`PIN` reservados para quando existir um segredo armazenado."""

    CPF_VEICULO = "CPF_VEICULO"
    BIOMETRIA = "BIOMETRIA"
    PIN = "PIN"
