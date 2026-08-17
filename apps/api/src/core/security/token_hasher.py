from __future__ import annotations

import hashlib


def hash_token(token: str) -> str:
    """Hash de referência para um token já assinado (JWT) — usado por `sessoes_mobile.token_acesso_
    hash` (D407). SHA-256, não `bcrypt`: o token nunca é "verificado" contra este hash (a
    assinatura do próprio JWT já cumpre esse papel) — é só a garantia de nunca guardar o token em
    texto claro (dictionary, `SESSAO_MOBILE.TOKEN_ACESSO_HASH`); `bcrypt` (`password_hasher.py`) é
    reservado para segredos curtos verificados por igualdade, o que não é o caso aqui.
    """

    return hashlib.sha256(token.encode()).hexdigest()
