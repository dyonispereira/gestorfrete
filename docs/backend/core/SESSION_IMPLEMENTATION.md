# SESSION_IMPLEMENTATION.md — Login, JWT, Sessão, Actor Context

Conecta a Foundation (`core.security.JWTTokenService`, `interfaces.dependencies.auth.
get_current_actor`, Lote 1) ao domínio real pela primeira vez. Traduz `docs/api/001-authentication.md`
(congelado) — bounded context `identity_access`.

## `domain/entities/session.py`

```python
class Session(BaseAggregateRoot[uuid.UUID]):
    user_id: uuid.UUID
    started_at: datetime
    expires_at: datetime
    ended_reason: EndedReason | None    # Logout / RevogacaoAdministrativa
    status: SessionStatus               # ATIVA/EXPIRADA/ENCERRADA

    def end(self, reason: EndedReason) -> None:
        if self.status != SessionStatus.ATIVA:
            raise ConflictError("IDENTITY_SESSION_ALREADY_ENDED", "...")
        self.status = SessionStatus.ENCERRADA
        self.ended_reason = reason
        self.record_event(SessaoDeAcessoEncerrada(session_id=self.id, reason=reason))

    def is_valid(self, now: datetime) -> bool:
        return self.status == SessionStatus.ATIVA and now < self.expires_at
```

**A sessão não armazena permissões** — obrigatório, pedido explícito do usuário e já garantido pela
própria coluna física (`sessoes_acesso` não tem coluna de permissão, `AUTHENTICATION.md`: "RBAC
sempre resolvido ao vivo"). Não existe nenhum campo `permission_codes`/`scopes` nesta entidade.

## Fluxo completo — `POST /auth/login`

```
1. LoginCommand(email, password) chega no handler — sem tenant_id (D208, resolvido pelo e-mail)
2. UserRepository.get_by_email(email) — busca cross-tenant (uq_usuarios_tenant_id_email é composta,
   mas o login não sabe o tenant ainda) — só possível porque email é indexado globalmente para esse
   propósito específico; resultado é (user, tenant_id) ou None
3. Credenciais inválidas OU usuário não encontrado → MESMA resposta genérica
   IDENTITY_INVALID_CREDENTIALS (401) — nunca revela qual dos dois faltou (ERROR_MODEL.md)
4. user.status == BLOQUEADO → 403 IDENTITY_USER_BLOCKED
   user.status == INATIVO   → 403 IDENTITY_USER_INACTIVE
5. PasswordHasher.verify(password, user.senha_hash) — falha cai no mesmo 401 genérico do passo 3
6. Session.create(user_id=user.id, expires_at=now + policy) — grava em sessoes_acesso
7. JWTTokenService.issue_access_token(
       subject=str(user.id),
       claims={"tenant_id": str(tenant_id), "session_id": str(session.id)},
   )
8. Refresh token: mesmo JWTTokenService, TTL maior, claims mínimas ({"sub", "session_id"}) — nunca
   tenant_id sozinho basta para nada sem o access token também ser válido
9. Resposta: {access_token, refresh_token, expires_in, user: User}
```

**JWT nunca carrega uma cópia de permissões** (D340) — claims são só `sub` (user_id), `tenant_id`,
`session_id`, `iat`, `exp`. Isso já era verdade na Foundation (Lote 1) para `tenant_id`/`sub`; este
lote adiciona `session_id` como o único claim novo.

## `AuthenticatedActor` ganha `session_id`

```python
@dataclass(frozen=True)
class AuthenticatedActor:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    session_id: uuid.UUID     # novo neste lote
```

`interfaces.dependencies.auth.get_current_actor` (Lote 1) passa a: decodificar `session_id` do
claim, **carregar a Session real e checar `is_valid(now)`** antes de montar o Actor — uma sessão
revogada/expirada faz o JWT (mesmo com assinatura válida e não expirado por `exp`) ser rejeitado
com `401 IDENTITY_SESSION_REVOKED`. Isso é o que faz "Session Revocation" (critério de conclusão do
usuário) funcionar mesmo com um `access_token` de curta duração ainda dentro do prazo.

```
Request
  ↓
Authorization: Bearer <jwt>
  ↓
JWTTokenService.decode_access_token  → claims (sub, tenant_id, session_id)
  ↓
SessionRepository.get_by_id(session_id)  → Session | None
  ↓
session is None OR not session.is_valid(now)?  → 401 IDENTITY_SESSION_REVOKED
  ↓
set_current_tenant_id(tenant_id)
  ↓
yield AuthenticatedActor(user_id, tenant_id, session_id)
```

## `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`

- **`refresh`**: decodifica o refresh token, resolve a `Session`, confirma `is_valid`, emite um
  **novo par** de tokens — não estende a mesma sessão indefinidamente (`expires_at` da Session é
  recalculado, mas a Session em si continua sendo a mesma linha, só sua janela de validade avança).
- **`logout`**: `Session.end(EndedReason.LOGOUT)` — sempre a sessão do próprio `actor.session_id`,
  nunca aceita um `session_id` de outro usuário no corpo.
- **`me`**: `{user, tenant: TenantContext, session: Session}` — `user.roles` expandido
  (`AuthorizationService.get_permission_codes` não é chamado aqui; o contrato pede nomes de Papel,
  não códigos de permissão — `RoleRepository.get_many(user.role_ids)` resolve os nomes).

## `POST /auth/forgot-password` / `POST /auth/reset-password`

Fora do escopo de testes obrigatórios deste lote (o contrato já define o fluxo, `001-
authentication.md`), mas implementados porque já estão congelados e são pequenos: geram/consomem um
token de reset de uso único (mesmo `JWTTokenService`, TTL curto, claim `purpose: "password_reset"`
para nunca ser aceito como access token por engano — checado explicitamente no handler de reset,
não confiado à validação genérica). `reset-password` bem-sucedido encerra **todas** as sessões
ativas do usuário (`001-authentication.md`, linha 151) — `SessionRepository.end_all_for_user(user_id,
EndedReason.PASSWORD_RESET)`.

## Testes obrigatórios deste bounded context

- Login com credenciais corretas → `200` + JWT decodificável com os 3 claims esperados.
- Login com e-mail inexistente vs. senha errada → **mesmo** `401 IDENTITY_INVALID_CREDENTIALS` nos
  dois casos (asserção explícita de que a mensagem não diferencia).
- Login de usuário `BLOQUEADO`/`INATIVO` → `403` com o código certo.
- Token expirado (`exp` no passado) → `401` (já coberto na Foundation, reconfirmado aqui end-to-end).
- **Session Revocation**: logout, depois nova requisição com o **mesmo** access_token (ainda dentro
  do `exp`) → `401 IDENTITY_SESSION_REVOKED`, não `200`.
- `refresh` com token de uma sessão já encerrada → `401 IDENTITY_REFRESH_TOKEN_INVALID`.
- `GET /auth/me` retorna `roles` com nomes expandidos, não IDs crus.
- Ponta a ponta: `POST /auth/login` → `GET /auth/me` → `GET /tenant` (RBAC) → `GET /users` (RBAC) —
  o fluxo completo pedido no critério de conclusão do Lote 2.
