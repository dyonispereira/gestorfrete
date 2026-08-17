# BACKEND_ARCHITECTURE.md — Visão Geral (Sprint 11, Lote 1)

Contraparte executável de [`docs/architecture/`](../architecture/) (Fase 0 — o "porquê"). Este
diretório (`docs/backend/`) documenta o "como": o que existe de fato em `apps/api/src/`, testado e
rodando. Onde os dois divergirem, `docs/backend/` é a fonte de verdade — código real supera
documento conceitual escrito antes de qualquer linha existir.

## D332/D333 — a OpenAPI congelada é o contrato do Backend

Registrado no início deste lote: **D332** — nenhum endpoint de negócio entra no Backend sem existir
antes em `docs/api/openapi.yaml` (congelado, `OPENAPI_FREEZE.md`, D329), salvo endpoints técnicos
explicitamente classificados como infraestrutura (`/health`, `/health/live`, `/health/ready` —
únicos exemplos até agora, deliberadamente fora de `/api/v1` e fora do contrato de negócio).
**D333** — nenhuma necessidade descoberta durante a implementação altera `openapi.yaml`
silenciosamente; o fluxo é sempre Achado → Decisão → Atualização da fonte → Propagação → Nova
versão do contrato, nunca "ajustar o YAML para o código caber".

## Stack técnica (confirmada, não aspiracional)

| Camada | Tecnologia | Onde |
|---|---|---|
| Framework HTTP | FastAPI 0.115 | `src/main.py`, `src/interfaces/` |
| ORM/Driver | SQLAlchemy 2.0 (async) + asyncpg | `src/core/database/` |
| Migrations | Alembic | `alembic/` |
| Cache/coordenação | Redis (`redis.asyncio`) | `src/core/cache/` |
| Mensageria/Event Bus | RabbitMQ (`aio-pika`) | `src/core/messaging/` |
| Storage | MinIO (S3-compatible) | `src/core/storage/` |
| Autenticação | JWT (`python-jose`) + bcrypt (`passlib`) | `src/core/security/` |
| Configuração | `pydantic-settings` | `src/core/config/` |
| Testes | `pytest` + `pytest-asyncio` + `httpx`/`TestClient` | `tests/` |
| Lint/Types | `ruff` + `mypy --strict` | `pyproject.toml` |
| Regra de dependência (mecânica) | `import-linter` | `pyproject.toml` `[tool.importlinter]` |

Todas as versões são as já fixadas em `pyproject.toml` desde a Fase 0 — nenhuma trocada nesta
etapa, exceto **`bcrypt` fixado em `^4.0.1`** (achado real deste lote, ver
[`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md)).

## Estrutura real de `apps/api/src/`

```
src/
├── core/                    # infraestrutura transversal — nunca conhece regra de negócio
│   ├── config/               # Settings (pydantic-settings), única fonte de env vars
│   ├── database/              # engine/session/UnitOfWork/health check (SQLAlchemy async)
│   ├── cache/                  # cliente Redis + health check
│   ├── messaging/               # conexão RabbitMQ + RabbitMQEventBus + health check
│   ├── storage/                  # cliente MinIO + health check
│   ├── security/                   # JWTTokenService, BcryptPasswordHasher, ports (Protocol)
│   ├── multitenancy/                 # ContextVar de tenant corrente
│   ├── observability/                 # logging JSON estruturado, request_id/correlation_id
│   └── exceptions/                     # hierarquia de erro + handlers FastAPI (ERROR_MODEL.md)
├── shared_kernel/            # building blocks DDD/CQRS — zero dependência de core/modules
│   ├── domain/                # BaseEntity, BaseAggregateRoot, BaseValueObject, DomainEvent,
│   │                           # Result, Specification, Repository[T], AuthenticatedActor
│   ├── application/            # Command/CommandHandler/InMemoryCommandBus,
│   │                            # Query/QueryHandler/InMemoryQueryBus, EventBus (porta)
│   └── infrastructure/          # UnitOfWork (porta)
├── interfaces/                # composition root HTTP — o único lugar que conhece FastAPI
│   ├── api/                    # health router (`/health*`) + `v1/router.py` (agrega módulos)
│   ├── middlewares/              # RequestContextMiddleware
│   └── dependencies/              # get_current_actor (JWT → AuthenticatedActor → tenant)
├── modules/                   # 25 pastas de bounded context oficiais — ver Lote 1.1 abaixo
│   └── <contexto>/domain|application|infrastructure|interfaces/  # todos ainda vazios (só __init__.py)
└── main.py                    # application factory — único ponto que monta tudo
```

## `main.py` — o que `create_app()` faz de verdade

```
configure_logging()               (JSON estruturado, nível de docs/backend/OBSERVABILITY.md)
        ↓
get_settings()                    (pydantic-settings, .env)
        ↓
FastAPI(lifespan=lifespan)        (ver TRANSACTION_MODEL.md — conexões são lazy, não eager)
        ↓
register_exception_handlers(app)  (ERROR_HANDLING.md)
        ↓
add_middleware(RequestContextMiddleware)
        ↓
include_router(health_router)     (/health, /health/live, /health/ready)
        ↓
include_router(api_router_v1)     (/api/v1/* — vazio nesta etapa, D332)
```

## Reconciliação do scaffold `modules/` — Sprint 11, Lote 1.1 (concluída)

A árvore `apps/api/src/modules/` tinha **30 pastas**, criadas na Fase 0 (antes do Domain Model/RBAC
rigorosos do Sprint 09/10 existirem). Auditada contra `RBAC_MATRIX.md`, `docs/domain/`,
`docs/database/`, `docs/api/openapi.yaml` e `docs/product/PRODUCT_MAP.md` — **D334**: uma pasta
criada durante a Foundation não representa um bounded context por si só; um módulo só é real quando
tem correspondência em Domain, Dictionary, Relational, RBAC e/ou OpenAPI conforme sua natureza.

### Removidas — scaffold sem lastro, sem código real, sem nenhuma referência no codebase

`landing/`, `marketplace/`, `telemetry/`, `workflow/` — confirmadas vazias (só `__init__.py`
padrão, nenhum arquivo `.py` com conteúdo real) e sem nenhum import em `src/`/`tests/` (buscado
mecanicamente antes da remoção). Nenhuma corresponde a um bounded context oficial:

- **`landing`**: "Landing Page" existe em `PRODUCT_MAP.md` (categoria "Portais Externos") — mas o
  próprio `PRODUCT_MAP.md` é explícito ("isto não é a arquitetura de código") e nenhuma entidade de
  Domain/RBAC/OpenAPI existe para isso ainda (Sprint 18 do roadmap do usuário, não modelado).
- **`marketplace`**: "Marketplace de Cargas" é uma **área** dentro da categoria "Comercial e CRM"
  em `PRODUCT_MAP.md`, nunca um bounded context próprio — sem entidade, RBAC ou endpoint dedicado.
- **`telemetry`**: Telemetria é uma **capacidade** do bounded context `tracking`
  (`RBAC_MATRIX.md` §7.16 já inclui "Telemetria"; `domain/008-rastreamento.md` também), nunca um
  bounded context separado — confirmado por `PRODUCT_MAP.md` agrupar "Telemetria de Veículo" dentro
  de "Rastreamento e Telemetria", uma única categoria.
- **`workflow`**: "Fluxos de Aprovação"/"Automações Configuráveis" existem como categoria de
  produto, mas cada aprovação real já vive dentro do bounded context dono (`maintenance.
  cost_approval.*`, `financial.payable.approve`/`.reject`) — não existe (ainda) um motor de
  workflow genérico com Domain/RBAC/OpenAPI próprios.

**D337**: nenhuma das quatro entra em `modules/` como pasta implementável enquanto não for um
bounded context oficial com escopo aprovado (Domain/Dictionary/Relational/RBAC/OpenAPI).

### Reclassificada — `notifications/` → `core/notification_delivery/`

**D336**: `notification_center` (`RBAC_MATRIX.md` §7.24, `docs/api/086-notifications.md`, Domain
Bloco 7/D323) é o único bounded context oficial de notificação — confirmado dono das entidades
`Notificação`/`Preferência de Canal de Notificação`. `modules/notifications/` (scaffold vazio,
duplicata de nome) foi removida; o conceito que ela representava — o mecanismo de **entrega**
efetiva (push/e-mail/in-app), não a decisão de negócio de notificar — agora tem um lugar real:
[`core/notification_delivery/`](../../apps/api/src/core/notification_delivery/__init__.py), ao
lado de `core/storage`/`core/messaging` (mesma natureza: adapter de infraestrutura transversal,
nunca um segundo bounded context concorrendo com `notification_center`).

### Mantidas — as 25 pastas restantes

```
ai analytics audit billing crm documents drivers financial fleet freight
identity_access integration maintenance mobile notification_center onboarding
pricing reporting routing settings storage subscription support tenancy tracking
```

Todas correspondem a um bounded context com lastro real. Uma diferença pontual vale registrar
(não corrigida — D335 pede reconciliar o que já existe, não criar o que falta, D-mesmo princípio
de "não criar novos bounded contexts"): esta lista tem **`settings`** (Domain/Dictionary/Relational
confirmam 4 entidades — Configuração Regional/Numeração/Personalização/Recurso Habilitado — mas
sem RBAC/endpoint dedicado ainda, D334's cláusula "e/ou" cobre isso) onde `RBAC_MATRIX.md` sozinho
listaria **`platform`** (§7.26, Administração da Plataforma cross-tenant) em seu lugar —
`platform` não tem pasta em `modules/` porque nunca teve (é a ferramenta interna da própria equipe
GestorFrete, um front distinto, `OPENAPI_FREEZE.md` Seção 1) e não foi criada agora, por não ter
sido pedido.

## Como este diretório cresce

Um documento por vez, mesmo princípio do resto do projeto. Quando o Lote 2 começar a escrever
código real em `modules/identity_access/`, os primeiros exemplos concretos (não apenas contratos)
de Domain/Application/Infrastructure/Interfaces entram nos documentos correspondentes.
