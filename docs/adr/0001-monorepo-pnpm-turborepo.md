# ADR 0001: Monorepo com pnpm workspaces + Turborepo

## Status
Aceito

## Contexto
O frontend (Next.js) e futuros pacotes compartilhados (`ui`, `types`, `config`) precisam evoluir
juntos, com mudanças de contrato (tipos, componentes) refletidas imediatamente entre eles. O
backend (Python/FastAPI) tem seu próprio ecossistema de dependências e vive no mesmo repositório
por conveniência operacional, mas não faz parte do workspace JavaScript.

## Decisão
Usar **pnpm workspaces** para gerenciar `apps/web` e `packages/*` como um único workspace
JavaScript/TypeScript, e **Turborepo** para orquestrar e cachear as tarefas (`build`, `lint`,
`typecheck`, `dev`) entre eles.

## Alternativas consideradas
- **npm workspaces sem Turborepo**: mais simples, mas sem cache incremental de build — conforme o
  número de pacotes compartilhados crescer (hoje 3: `ui`, `types`, `config`), o tempo de build/lint
  cresceria linearmente sem necessidade.
- **Repositórios separados para frontend e backend**: isolamento total, mas maior fricção para
  versionar mudanças de contrato entre API e frontend, especialmente quando `packages/types` passar
  a ser gerado a partir do OpenAPI da API.

## Consequências
- `pnpm-workspace.yaml` declara `apps/*` e `packages/*` como membros do workspace.
- `turbo.json` declara o grafo de tarefas (`build` depende de `^build` dos pacotes internos, etc.).
- O backend Python (`apps/api`) fica fora do workspace pnpm — é gerenciado por Poetry
  independentemente (ver [ADR 0002](./0002-python-poetry.md)).
