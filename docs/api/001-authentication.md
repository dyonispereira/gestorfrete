# 001 — Authentication

Bounded context proprietário: `identity_access` (D215 — único dono destes 6 endpoints). Nenhum
endpoint de MFA aqui — `fatores_autenticacao` já existe no Modelo Relacional (D120-style,
extensível) mas o *fluxo* de login com segundo fator não está formalizado em nenhum flow de
domínio ainda; inventar o contrato HTTP antes da regra existir violaria D101/D103. Quando o fluxo de
MFA for decidido, este documento ganha os endpoints correspondentes.

## `POST /api/v1/auth/login`

Autentica um Usuário e inicia uma sessão (`sessoes_acesso`).

**Segurança**: nenhuma (pré-autenticação) — ver `components/security.md`.

**Request**

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          email: { type: string, format: email }
          password: { type: string, format: password }
        required: [email, password]
```

**Responses**

| Código | Corpo |
|---|---|
| `200` | `{ access_token, refresh_token, expires_in, user: User }` — ver `components/schemas.md` |
| `400` | `BadRequest` — `email`/`password` ausentes |
| `401` | `Unauthorized` — `IDENTITY_INVALID_CREDENTIALS` (mensagem genérica — nunca diferencia "e-mail não existe" de "senha errada", `ERROR_MODEL.md`) |
| `403` | `Forbidden` — `IDENTITY_USER_BLOCKED` (usuário com `bloqueios_acesso` vigente) ou `IDENTITY_USER_INACTIVE` |
| `429` | `TooManyRequests` — política mais agressiva que qualquer outro endpoint (`RATE_LIMITING.md`, categoria Login) |
| `500` | `InternalServerError` |

Tenant é resolvido a partir do `email` (único por `(tenant_id, email)`, `CONSTRAINTS.md`) — o
cliente nunca informa `tenant_id` no login (D208), mesmo sendo tecnicamente o primeiro ponto de
contato sem sessão ainda estabelecida.

## `POST /api/v1/auth/refresh`

Troca um refresh token válido por um novo par de tokens.

**Segurança**: nenhuma via `bearerAuth` — o próprio refresh token (enviado no corpo ou cookie
`httpOnly`, conforme a superfície, `AUTHENTICATION.md`) é a credencial.

**Request**

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          refresh_token: { type: string }
        required: [refresh_token]
```

**Responses**

| Código | Corpo |
|---|---|
| `200` | `{ access_token, refresh_token, expires_in }` |
| `401` | `Unauthorized` — `IDENTITY_REFRESH_TOKEN_INVALID` (expirado, revogado, ou sessão encerrada) |
| `500` | `InternalServerError` |

## `POST /api/v1/auth/logout`

Encerra a sessão atual (`sessoes_acesso.status → ENCERRADA`, `motivo_encerramento = Logout`).

**Segurança**: `bearerAuth`. Sem RBAC adicional — todo Usuário autenticado pode encerrar a própria
sessão (Escopo "Próprio usuário", D053).

**Responses**

| Código | Corpo |
|---|---|
| `204` | Sem corpo |
| `401` | `Unauthorized` |
| `500` | `InternalServerError` |

## `POST /api/v1/auth/forgot-password`

Inicia o fluxo de redefinição de senha — envia um token de reset por e-mail.

**Segurança**: nenhuma (pré-autenticação).

**Request**

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          email: { type: string, format: email }
        required: [email]
```

**Responses**

| Código | Corpo |
|---|---|
| `200` | `{ message: "Se o e-mail existir, um link de redefinição foi enviado." }` — **sempre** a mesma mensagem, exista ou não o e-mail (nunca revela se um e-mail está cadastrado, mesmo princípio de `IDEMPOTENCY.md`/`ERROR_MODEL.md` de não vazar existência) |
| `429` | `TooManyRequests` — evita abuso do envio de e-mail |
| `500` | `InternalServerError` |

Nunca retorna `404` para e-mail inexistente — sempre `200` com a mesma mensagem genérica.

## `POST /api/v1/auth/reset-password`

Conclui a redefinição usando o token recebido por e-mail.

**Segurança**: nenhuma via `bearerAuth` — o token de reset (de uso único, curto prazo) é a
credencial.

**Request**

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          token: { type: string }
          new_password: { type: string, format: password, minLength: 8 }
        required: [token, new_password]
```

**Responses**

| Código | Corpo |
|---|---|
| `200` | `{ message: "Senha redefinida com sucesso." }` |
| `400` | `BadRequest` — senha não atende aos requisitos mínimos |
| `409` | `Conflict` — `IDENTITY_RESET_TOKEN_ALREADY_USED` (token de uso único já consumido) |
| `422` | `UnprocessableEntity` — `IDENTITY_RESET_TOKEN_EXPIRED` |
| `500` | `InternalServerError` |

Toda sessão ativa do Usuário (`sessoes_acesso`) é encerrada ao concluir o reset — redefinir a senha
invalida qualquer sessão obtida com a senha antiga.

## `GET /api/v1/auth/me`

Retorna o Usuário autenticado, seu `TenantContext` e a sessão atual.

**Segurança**: `bearerAuth`. Sem RBAC adicional (Escopo "Próprio usuário").

**Responses**

| Código | Corpo |
|---|---|
| `200` | `{ user: User, tenant: TenantContext, session: Session, roles: string[] }` |
| `401` | `Unauthorized` |
| `500` | `InternalServerError` |

**Achado do Frontend Lote 1 (Sprint 12)**: este parágrafo dizia que `user.roles` viria "expandido
(nomes dos Papéis, não só IDs)" para o Frontend montar a UI de RBAC sem uma segunda chamada — a
implementação real (`auth_schemas.py::MeResponse`) não faz isso: `user.roles` continua como UUIDs, e
o que existe é um campo `roles` separado no nível raiz com só os *nomes* dos Papéis (conveniência de
exibição, ex.: mostrar "Papel: Administrador" no menu do usuário) — não os *códigos de permissão*.
Nomes de Papel sozinhos não permitem montar o menu autorizado; o Frontend ainda precisa de
`GET /roles/{id}` por Papel para resolver os `permission codes` reais (ver
`core/rbac/permissions-provider.tsx` no Frontend). Contrato (`openapi.yaml`) atualizado para
declarar o `roles` real; a lacuna de design (se `/auth/me` deveria devolver permission codes
diretamente, cumprindo a intenção original deste parágrafo) fica para decisão explícita no Lote 2
do Frontend (Auth + Tenant + Usuários + RBAC) — não corrigida aqui unilateralmente, já que o Backend
está congelado (D427/D428/D429).

## Como este documento cresce

Endpoint de MFA entra aqui quando `fatores_autenticacao` ganhar um flow de domínio formalizado —
nunca antes disso (mesma disciplina de D101/D103 aplicada à API).
