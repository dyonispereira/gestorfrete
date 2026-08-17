# Clean Architecture

## A regra de dependência

Dentro de cada bounded context (`apps/api/src/modules/<contexto>/`), o código é dividido em 4
camadas concêntricas. A regra é simples e não-negociável: **dependências de código-fonte só podem
apontar para dentro**. Uma camada mais interna nunca conhece nem importa nada de uma camada mais
externa.

```
 ┌─────────────────────────────────────────────┐
 │ interfaces      (FastAPI routers, schemas)   │  ← mais externo
 │  ┌───────────────────────────────────────┐   │
 │  │ infrastructure (SQLAlchemy, RabbitMQ)  │   │
 │  │  ┌─────────────────────────────────┐  │   │
 │  │  │ application (commands, queries) │  │   │
 │  │  │  ┌───────────────────────────┐  │  │   │
 │  │  │  │ domain (entities, VOs)    │  │  │   │  ← mais interno
 │  │  │  └───────────────────────────┘  │  │   │
 │  │  └─────────────────────────────────┘  │   │
 │  └───────────────────────────────────────┘   │
 └─────────────────────────────────────────────┘
```

## As 4 camadas

### `domain/`
As regras de negócio puras. Entidades, Value Objects, Domain Events e as **interfaces** (ports) de
repositório. Não importa FastAPI, SQLAlchemy, nem nenhuma biblioteca de infraestrutura — é Python
puro. Isso é o que torna as regras de negócio testáveis sem subir banco, fila ou servidor HTTP.

### `application/`
Orquestra o domínio para realizar casos de uso, divididos em `commands/` (escrita) e `queries/`
(leitura) — ver [`cqrs.md`](./cqrs.md). Depende do `domain/`, nunca do `infrastructure/` ou do
`interfaces/` — ao invés disso, depende das **interfaces** que o `domain/` declara (Repository
Pattern), e recebe a implementação concreta via injeção de dependência.

### `infrastructure/`
Implementa os contratos declarados nas camadas internas: os repositórios concretos com SQLAlchemy
(`persistence/`) e os publishers/consumers de RabbitMQ (`messaging/`). É a única camada que sabe
que o banco é PostgreSQL ou que a fila é RabbitMQ — se um dia trocarmos de tecnologia, a mudança
fica contida aqui.

### `interfaces/`
A camada de apresentação: routers FastAPI (`api/`) e schemas Pydantic de request/response
(`schemas/`). Traduz HTTP em chamadas para a `application/` e o resultado da `application/` de
volta em HTTP. Não contém regra de negócio nenhuma.

## Repository Pattern

O `domain/repositories/` de cada módulo declara **interfaces** (ex: `FreightRepository`) descrevendo
o que o domínio precisa persistir, sem saber como. A implementação concreta
(`infrastructure/persistence/repositories/`) sabe o "como" (SQLAlchemy + PostgreSQL). Isso permite
testar `application/` com um repositório fake em memória, sem precisar de banco real.

## Shared Kernel

Nem tudo é específico de um bounded context. `shared_kernel/` (fora de `modules/`) concentra as
base classes reutilizadas por todos: `BaseEntity`, `BaseValueObject`, `BaseAggregateRoot`,
`DomainEvent` (domain), `Command`/`Query`/`EventBus` (application) e `UnitOfWork` (infrastructure).
Qualquer bounded context pode depender do `shared_kernel/`, mas o `shared_kernel/` nunca depende de
um bounded context específico.
