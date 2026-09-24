# CI_PIPELINE.md — Barreira mínima antes de qualquer deploy

V1 Operational Hardening — item de INFRA pedido explicitamente pelo usuário: "não precisa criar
uma plataforma DevOps complexa. Quero somente a barreira mínima de segurança para impedir deploy
de build quebrada." Não existia nenhum workflow de CI antes deste documento (`.github/workflows/`
vazio) — todo o deploy era manual, sem nenhuma verificação automática interposta, P0 registrado no
Go-Live Audit.

Este documento é o contrato do pipeline; a implementação (`.github/workflows/ci.yml`) roda
exatamente os comandos já usados manualmente durante todo este projeto para verificar cada rodada
de trabalho — nenhum comando novo, nenhuma ferramenta nova.

## O que o pipeline verifica (backend, `apps/api/`)

| Passo | Comando | Falha o build se |
|---|---|---|
| Lint | `poetry run ruff check .` | Qualquer violação de estilo/import não resolvida |
| Tipos | `poetry run mypy src` | Qualquer erro de tipo (as 7 exceções pré-existentes de stub ausente `jose`/`passlib` ficam com `# type: ignore` explícito ou permanecem a única exceção conhecida documentada aqui, nunca silenciadas em massa) |
| Fronteiras de módulo | `PYTHONPATH=src poetry run lint-imports` | Qualquer contrato de `import-linter` quebrado (D090/D149/D161/D285/D421/D426, `DEPENDENCY_RULES.md`) |
| Migrations aplicam limpo | `poetry run alembic upgrade head` contra um Postgres efêmero (serviço do próprio job de CI, não o banco de desenvolvimento) | Qualquer migration que não aplique em banco vazio |
| Testes | `poetry run pytest tests/unit tests/integration -q` e `poetry run pytest tests/ -m integration -q` contra o mesmo Postgres/Redis efêmeros | Qualquer teste vermelho |

## O que o pipeline verifica (frontend, `apps/web/` + `packages/*`)

| Passo | Comando | Falha o build se |
|---|---|---|
| Tipos | `pnpm typecheck` (roda em todos os workspaces via Turbo) | Qualquer erro de TypeScript |
| Lint | `pnpm lint` (`next lint`) | Qualquer warning/erro do ESLint |
| Build | `pnpm build` | Build de produção do Next.js falhar |

## E2E (`apps/web/e2e/`)

```bash
docker compose -f infra/compose/docker-compose.yml up -d
docker compose -f infra/compose/docker-compose.yml exec -T api poetry run alembic upgrade head
npx playwright test  # workers: 1, sequencial — mesma configuração já usada localmente
```

Roda contra a stack completa via `docker-compose.yml` (mesmo ambiente usado manualmente durante
todo este projeto), não um mock — é a suíte que mais realisticamente reproduz produção,
propositalmente mais lenta e rodando por último, depois que os passos rápidos acima já filtraram a
maioria dos problemas.

## Esboço do workflow (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4-alpine
        env: { POSTGRES_USER: gestorfrete, POSTGRES_PASSWORD: gestorfrete, POSTGRES_DB: gestorfrete }
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U gestorfrete" --health-interval 5s --health-timeout 5s --health-retries 10
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
        options: --health-cmd "redis-cli ping" --health-interval 5s --health-timeout 5s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install poetry==1.8.3
      - working-directory: apps/api
        run: poetry install
      - working-directory: apps/api
        run: poetry run ruff check .
      - working-directory: apps/api
        run: poetry run mypy src
      - working-directory: apps/api
        run: PYTHONPATH=src poetry run lint-imports
      - working-directory: apps/api
        run: poetry run alembic upgrade head
      - working-directory: apps/api
        run: poetry run pytest tests/ -m integration -q

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20", cache: "pnpm" }
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm lint
      - run: pnpm build

  e2e:
    needs: [backend, frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f infra/compose/docker-compose.yml up -d
      - run: docker compose -f infra/compose/docker-compose.yml exec -T api poetry run alembic upgrade head
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20", cache: "pnpm" }
      - working-directory: apps/web
        run: pnpm install --frozen-lockfile && npx playwright install --with-deps && npx playwright test
```

Três jobs, `backend`/`frontend` em paralelo, `e2e` só depois dos dois passarem (a barreira cara
roda por último, nunca bloqueia feedback rápido de lint/tipo). Branch protection em `main` exige os
três jobs verdes antes de merge — esse é o mecanismo real de "impedir deploy de build quebrada"
pedido pelo usuário; nenhum passo de deploy automático está incluído aqui (fora de escopo
explícito, "não precisa criar uma plataforma DevOps complexa").

## Health checks pós-deploy (já existentes, só referenciados aqui)

`/health/live` (liveness — processo responde) e `/health/ready` (readiness — Postgres + Redis
alcançáveis, `check_database_connection`/`check_redis_connection`) já existem e são bem desenhados
(`OBSERVABILITY.md`). O pipeline acima não os chama diretamente (não há passo de deploy real
ainda), mas qualquer mecanismo de deploy futuro deve gatear o cutover de tráfego em
`/health/ready`, nunca só em "o processo subiu".

## Fora de escopo desta rodada (não esquecido)

- Deploy automático (CD) — só a barreira de CI (build quebrada nunca chega a `main`), sem o próximo
  passo de promover automaticamente para produção.
- Cache de dependências entre execuções do CI (acelera, não muda o que é verificado) — otimização,
  não correção.
- Notificação de falha (Slack/e-mail) — GitHub já notifica por padrão via PR status checks;
  integração adicional fica para quando houver necessidade real.
