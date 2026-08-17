# GestorFrete ERP Enterprise

ERP multi-tenant para transportadoras, construído para crescer ao longo de vários meses e atender
futuramente milhares de empresas clientes.

> **Status: fundação arquitetural.** Este repositório contém apenas estrutura, contratos e
> configuração — nenhuma tela, endpoint de API, modelo de banco de dados ou fluxo de login foi
> implementado ainda. Veja [`docs/architecture`](docs/architecture) para o porquê de cada decisão.

## Stack

| Camada | Tecnologias |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind, shadcn/ui |
| Backend | Python, FastAPI, SQLAlchemy, PostgreSQL, Redis, RabbitMQ, MinIO |
| Arquitetura | DDD, Clean Architecture, SOLID, Repository Pattern, CQRS, Event-Driven, Multi-Tenant |
| Infraestrutura | Docker, pnpm workspaces + Turborepo (frontend), Poetry (backend) |

## Estrutura do monorepo

```
apps/
  web/        Next.js — frontend, organizado por bounded context (feature-sliced)
  api/        FastAPI — backend, organizado por bounded context (DDD + Clean Architecture)
packages/
  ui/         Componentes shadcn/ui compartilhados
  config/     Configuração compartilhada (tsconfig, eslint, tailwind)
  types/      Tipos TypeScript compartilhados
infra/
  docker/     Dockerfiles das aplicações
  compose/    docker-compose.yml de infraestrutura local (Postgres, Redis, RabbitMQ, MinIO)
docs/
  architecture/  Explicação da arquitetura e do porquê de cada decisão
  product/       A "bíblia" de produto: visão, roadmap, regras de negócio, telas, NFRs
  database/      Modelo de dados (DER, tabelas, enums, índices, migrations, naming)
  api/           Contrato da API (REST, webhooks, eventos, erros, auth, versionamento)
  ux/            Design system (cores, componentes, ícones, layout, tipografia, animações)
  modules/       Uma spec por tela/funcionalidade, numeradas (preparado, ainda vazio)
  adr/           Architecture Decision Records
```

## Setup local

### Frontend
```bash
pnpm install
cp apps/web/.env.example apps/web/.env.local
pnpm dev
```

### Backend
```bash
cd apps/api
poetry install
cp .env.example .env
poetry run uvicorn main:app --app-dir src --reload
```

### Infraestrutura
```bash
cp infra/compose/.env.example infra/compose/.env
docker compose -f infra/compose/docker-compose.yml --env-file infra/compose/.env up -d
```

## Documentação

Comece por [`docs/architecture/README.md`](docs/architecture/README.md) para entender a arquitetura
completa e o porquê de cada pasta existir.
