# Arquitetura do GestorFrete ERP Enterprise

Este documento é o ponto de entrada para entender **por que** o projeto está estruturado do jeito
que está. Ele não descreve funcionalidades de negócio (ainda não existem) — descreve as decisões
estruturais tomadas nesta etapa de fundação e o raciocínio por trás de cada uma.

## Visão geral

O GestorFrete é um **ERP multi-tenant para transportadoras**, construído para crescer ao longo de
vários meses e eventualmente atender milhares de empresas clientes. Toda decisão de arquitetura
parte de uma pergunta: *"isso ainda vai fazer sentido quando tivermos 50 bounded contexts, 20
desenvolvedores e milhares de tenants?"*. Por isso a fundação prioriza:

1. **Isolamento por domínio** (DDD) em vez de organização técnica genérica (`controllers/`,
   `models/`, `views/` espalhados soltos).
2. **Regra de dependência única** (Clean Architecture): regras de negócio nunca dependem de
   framework, banco ou UI — é o inverso.
3. **Separação leitura/escrita** (CQRS) onde a complexidade do domínio justificar.
4. **Comunicação assíncrona entre domínios** (Event-Driven) em vez de acoplamento direto entre
   bounded contexts.
5. **Multi-tenancy como preocupação transversal desde o dia um**, não como algo para "adicionar
   depois".

## Como navegar a estrutura de pastas

```
apps/api           → backend (FastAPI) — ver clean-architecture.md e ddd.md
apps/web           → frontend (Next.js) — organização feature-sliced espelhando os mesmos domínios
packages/          → código compartilhado entre aplicações do monorepo
infra/             → containers de infraestrutura (Postgres, Redis, RabbitMQ, MinIO) e Dockerfiles
docs/architecture/ → este diretório — o porquê da arquitetura
docs/product/      → a "bíblia" de produto: visão, roadmap, regras de negócio, telas, NFRs
docs/database/     → modelo de dados, quando as primeiras tabelas forem desenhadas
docs/api/          → contrato REST/eventos/erros da API, quando os primeiros endpoints existirem
docs/ux/           → design system (cores, componentes, tipografia, animações)
docs/modules/      → uma spec por tela/funcionalidade, numeradas (preparado, ainda vazio)
docs/adr/          → registro histórico das decisões de ferramental
```

Os diretórios `docs/product/`, `docs/database/`, `docs/api/` e `docs/ux/` foram criados com
arquivos vazios propositalmente — são o destino de decisões que ainda serão tomadas nas próximas
etapas, não uma antecipação de conteúdo.

## Leitura recomendada, em ordem

1. [`ddd.md`](./ddd.md) — os bounded contexts do negócio e por que cada um existe
2. [`clean-architecture.md`](./clean-architecture.md) — as 4 camadas dentro de cada bounded context
3. [`cqrs.md`](./cqrs.md) — commands vs queries
4. [`event-driven.md`](./event-driven.md) — como os bounded contexts se comunicam
5. [`multi-tenancy.md`](./multi-tenancy.md) — como o isolamento entre transportadoras é garantido
6. [`security-rbac-lgpd.md`](./security-rbac-lgpd.md) — fundações de segurança e conformidade
7. [`../adr/`](../adr/) — registro histórico das decisões de ferramental já tomadas

## O que esta etapa **não** contém

Por decisão explícita, esta fundação **não** inclui: telas, componentes de negócio no frontend,
endpoints de API, modelos de banco de dados/migrations, ou qualquer fluxo de login. O que existe é
a estrutura, os contratos (interfaces) e a configuração necessários para que essas coisas sejam
adicionadas de forma consistente nas próximas etapas.
