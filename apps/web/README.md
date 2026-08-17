# GestorFrete Web

Frontend do GestorFrete ERP Enterprise: Next.js (App Router) + React + TypeScript + Tailwind +
shadcn/ui, organizado por domínio de negócio (feature-sliced), espelhando os bounded contexts do
backend (`apps/api`). Veja [`docs/architecture`](../../docs/architecture) na raiz do monorepo para
a explicação completa da arquitetura.

Esta é a etapa de **fundação**: existe estrutura, configuração de ferramentas e o design system
base, mas nenhuma tela, componente de negócio ou fluxo de login foi implementado ainda —
`src/app/` está intencionalmente vazio.

## Setup local

```bash
pnpm install
cp apps/web/.env.example apps/web/.env.local
pnpm --filter @gestorfrete/web dev
```

## Estrutura

- `src/app/` — rotas (App Router). Vazio nesta etapa.
- `src/modules/` — um diretório por bounded context (`components/`, `hooks/`, `services/`, `types/`)
- `src/shared/` — código reaproveitado por mais de um módulo
- `src/core/` — contextos transversais (auth, tenant, config) — fundação, sem lógica de login
- `src/styles/` — CSS global e variáveis de tema (Tailwind + shadcn)
