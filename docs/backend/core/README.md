# docs/backend/core — Sprint 11, Lote 2 (Core/Identity/Tenancy)

Documentação de implementação dos três pilares dos quais todo outro bounded context vai depender —
não repete o contrato de produto (`docs/api/001-authentication.md` a `005-permissions.md`, já
congelado) nem o RBAC (`docs/product/RBAC_MATRIX.md` §7.4/§7.5, já congelado): responde só "como
isso vira código" em `apps/api/src/modules/tenancy/` e `apps/api/src/modules/identity_access/`.

| Documento | Bounded context | Cobre |
|---|---|---|
| [`TENANCY_IMPLEMENTATION.md`](./TENANCY_IMPLEMENTATION.md) | `tenancy` | `Tenant` — `GET`/`PATCH /tenant` |
| [`IDENTITY_IMPLEMENTATION.md`](./IDENTITY_IMPLEMENTATION.md) | `identity_access` | `Usuário`/`Papel`/`Permissão`, `usuarios_papeis`, `papel_permissao` |
| [`AUTHORIZATION_IMPLEMENTATION.md`](./AUTHORIZATION_IMPLEMENTATION.md) | `identity_access` | `AuthorizationService`, resolução de RBAC ao vivo, `require_permission` |
| [`SESSION_IMPLEMENTATION.md`](./SESSION_IMPLEMENTATION.md) | `identity_access` | `Sessão`, login/refresh/logout/me, JWT → `AuthenticatedActor` |

## Como os quatro se encaixam

```
POST /auth/login  (SESSION_IMPLEMENTATION)
        ↓ emite JWT com {sub, tenant_id, session_id} — nunca permissões (D340)
get_current_actor  (Foundation, Lote 1, estendido neste lote com validação de Session)
        ↓
AuthenticatedActor {user_id, tenant_id, session_id}
        ↓
require_permission("...")  (AUTHORIZATION_IMPLEMENTATION) — resolve RBAC ao vivo
        ↓
Handler de Tenant/User/Role/Permission  (TENANCY_IMPLEMENTATION / IDENTITY_IMPLEMENTATION)
        ↓
Repository — sempre filtrado pelo tenant do Actor, nunca por um tenant_id de fora (D338/D339)
```

## Pré-requisito resolvido antes deste lote

Sprint 11 Lote 1.1 (`../BACKEND_ARCHITECTURE.md`) reconciliou `apps/api/src/modules/` para 25
pastas reais — este lote é o primeiro a efetivamente escrever código em duas delas (`tenancy/`,
`identity_access/`).

## Validação com PostgreSQL real

Ao contrário do Lote 1 (onde Docker esteve ausente do ambiente de execução e a conectividade real
ficou pendente), este lote **exigiu** banco real antes do fechamento — resolvido com um PostgreSQL
16 portátil (binários oficiais, sem serviço/instalador, sem admin, porta dedicada 5433, isolado de
qualquer outra instância na máquina) especificamente porque um `postgres.exe` já rodando na porta
padrão 5432 **não pertence a este projeto** (achado reportado ao usuário antes de qualquer
`CREATE DATABASE`, que escolheu explicitamente não tocar nele). Detalhe completo, incluindo os 6
bugs reais que a execução encontrou (DDL de `logs_auditoria`, colunas `datetime` sem timezone,
dependência ausente, quirk do FastAPI em `status_code=204`, contratos `import-linter` nunca
wireados, estado global de teste sem reset) em [`TESTING_STRATEGY.md`](../TESTING_STRATEGY.md).

## Achados deste lote (Sprint 11, Lote 2)

Encontrados só por execução real (nunca por inspeção de código) — cada um virou uma linha em
`DECISIONS.md`:

| # | Achado | Decisão |
|---|---|---|
| 1 | `EVENT_MAP.md` nunca catalogava eventos de `identity_access` | D345 |
| 2 | DDL de `logs_auditoria` inválida numa tabela `PARTITION BY RANGE` (PK sem a coluna de partição) | D346 |
| 3 | Colunas `datetime` mapeadas sem `timezone=True`, virando `TIMESTAMP` ingênuo | D347 |
| 4 | Contratos `import-linter` de `tenancy`/`identity_access` documentados mas nunca adicionados a `pyproject.toml` | D348 |
| 5 | `email-validator` ausente de `pyproject.toml`, exigido em runtime por `EmailStr` | D349 |
| 6 | Rotas `status_code=204` exigem `response_model=None` explícito no FastAPI 0.115 | D350 |
| 7 | `core.security.session_validation` sem reset, vazando estado global entre arquivos de teste | D351 |

## Estado final verificado

`ruff check src tests`, `mypy src` (568 arquivos, `strict`) e `lint-imports` (6/6 contratos) — todos
`PASS`. `pytest` completo (unit + integration, exceto Redis/RabbitMQ/MinIO, ausentes deste sandbox):
**59 passed, 0 failed**, incluindo os 8 cenários de teste explicitamente pedidos (Tenant Isolation,
RBAC, Role único, Roles múltiplos, Soft Delete, Session Revocation, JWT, Auditoria) e o fluxo
`POST /auth/login → JWT → GET /auth/me → endpoint protegido` de ponta a ponta contra o Postgres real.

## Decisões

D338–D351 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Como esta pasta cresce

Um documento por bounded context, mesmo princípio do resto do projeto. Próximo bounded context com
código real ainda não definido — depende da ordem de dependência real entre módulos
(`docs/product/DEPENDENCY_MAP.md`), a confirmar quando o Lote 3 for aberto.
