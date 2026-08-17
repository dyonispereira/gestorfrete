# GestorFrete API

Backend do GestorFrete ERP Enterprise: FastAPI + SQLAlchemy + PostgreSQL, organizado por
bounded contexts (DDD) seguindo Clean Architecture e CQRS. Veja
[`docs/architecture`](../../docs/architecture) (o porquê) e [`docs/backend`](../../docs/backend) (o
como, executável e testado) na raiz do monorepo.

**Sprint 11, Lote 1 — Backend Foundation concluído**: infraestrutura técnica real e testada
(config, banco/Unit of Work, cache, mensageria, storage, segurança, multi-tenancy, observabilidade,
tratamento de erro, health checks, regra de dependência aplicada mecanicamente via
`import-linter`).

**Sprint 11, Lote 2 — Core/Identity/Tenancy concluído**: primeiro bounded context com código de
negócio real — `Tenant`, `Usuário`, `Papel`, `Permissão`, `Sessão de Acesso`, RBAC resolvido ao vivo,
fluxo completo `POST /auth/login → JWT → GET /auth/me → endpoint protegido`. Validado com PostgreSQL
real (migrations + testes de integração), não apenas por inspeção — ver
[`docs/backend/README.md`](../../docs/backend/README.md#lote-2--coreidentitytenancy-concluído).
Sempre a partir do contrato já congelado em [`docs/api/openapi.yaml`](../../docs/api/openapi.yaml)
(D332/D333).

**Sprint 11, Lote 3 — Cadastros concluído**: `Cliente`/`Contato` (`crm`), `Fornecedor`
(`maintenance`), `Motorista`/`Documento` (`drivers`), `Funcionário` (`identity_access`), `Centro de
Custo` (`financial`) — mais `Endereço`, componente compartilhado novo (`src/shared/addresses/`).
Nenhum `modules/cadastros/` criado — cada agregado vive no bounded context que já o possuía por
RBAC. Ver [`docs/backend/README.md`](../../docs/backend/README.md#lote-3--cadastros-concluído).

## Requisitos

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- Infraestrutura local via `infra/compose/docker-compose.yml` (PostgreSQL, Redis, RabbitMQ, MinIO,
  e a própria API — os cinco sobem juntos desde o Lote 1)

## Setup local

```bash
cd apps/api
poetry install
cp .env.example .env
```

## Rodar a infraestrutura + API via Docker Compose

```bash
docker compose -f infra/compose/docker-compose.yml up -d --build
curl http://localhost:8000/health/ready
```

## Rodar a aplicação localmente (fora do Docker)

```bash
poetry run uvicorn main:app --app-dir src --reload
```

## Rodar os testes

```bash
poetry run pytest                 # unitários — não exigem infraestrutura viva
poetry run pytest -m integration   # exige Postgres real (`docker compose up`, ou um Postgres local
                                     # apontado por DATABASE_URL); os testes de identity_access/
                                     # tenancy rodam contra o banco real, sem mocks
```

Antes do primeiro `pytest -m integration`, rode as migrations contra o banco real:

```bash
poetry run alembic upgrade head
```

## Lint, tipos e regra de dependência

```bash
poetry run ruff check src tests
poetry run mypy src
PYTHONPATH=src poetry run lint-imports
```

## Estrutura

- `src/modules/` — 25 bounded contexts oficiais (domain, application, infrastructure, interfaces),
  reconciliado contra Domain/RBAC/OpenAPI no Lote 1.1 (removidas 4 pastas sem lastro + 1 duplicata,
  ver [`docs/backend/BACKEND_ARCHITECTURE.md`](../../docs/backend/BACKEND_ARCHITECTURE.md)).
  `tenancy`/`identity_access` (Lote 2) e `crm`/`maintenance`/`drivers`/`financial` (Lote 3) têm
  código real — os outros 19 ainda só `__init__.py`.
- `src/shared/` — componentes de negócio compartilhados entre módulos, sem bounded context/RBAC
  próprio (D354, novo desde o Lote 3) — hoje só `addresses/` (`Endereço`, usado por `crm`/
  `maintenance`). Nunca um bounded context disfarçado: não entra em `modules/`.
- `src/shared_kernel/` — building blocks de DDD/CQRS reutilizados por todos os módulos
  (`BaseEntity`/`BaseAggregateRoot`/`Result`/`Specification`/`Repository`, `Command`/`Query`/
  `EventBus`, `UnitOfWork`, `AuthenticatedActor`, `AuditMetadata`) — ver
  [`docs/backend/DOMAIN_LAYER.md`](../../docs/backend/DOMAIN_LAYER.md)/
  [`APPLICATION_LAYER.md`](../../docs/backend/APPLICATION_LAYER.md)
- `src/core/` — infraestrutura transversal (config, database, cache, messaging, storage, security,
  multitenancy, observability, exceptions, audit) — ver
  [`docs/backend/INFRASTRUCTURE_LAYER.md`](../../docs/backend/INFRASTRUCTURE_LAYER.md)
- `src/interfaces/` — composition root da API (health router, router `/api/v1`, middlewares,
  dependency de autenticação) — ver
  [`docs/backend/INTERFACES_LAYER.md`](../../docs/backend/INTERFACES_LAYER.md)
- `src/main.py` — application factory do FastAPI
- `alembic/` — 2 migrations reais (Lote 2: `tenants`/`usuarios`/`papeis`/`permissoes`/
  `usuarios_papeis`/`papel_permissao`/`sessoes_acesso`/`logs_auditoria`, esta última particionada
  por `data_hora`; Lote 3: `clientes`/`contatos_cliente`/`fornecedores`/`motoristas`/
  `documentos_motorista`/`funcionarios`/`centros_custo`/`enderecos`), aplicadas e verificadas contra
  PostgreSQL real
- `tests/` — `unit/` (48 testes, sem infraestrutura), `integration/` (marcados `@pytest.mark.
  integration`, exigem Postgres real — 10 testes de `identity_access`/`tenancy` desde o Lote 2, 9
  de Cadastros desde o Lote 3), `e2e/` (vazio ainda)
