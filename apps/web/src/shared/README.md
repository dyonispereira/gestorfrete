# Shared

Código de front-end reaproveitado por **mais de um módulo de negócio**. Nada aqui conhece regras
de negócio de um domínio específico — se um componente/hook/serviço só faz sentido para um módulo,
ele pertence a `modules/<módulo>/`, não aqui.

## Estrutura

- `components/` — primitivos de UI compartilhados (construídos sobre `shadcn/ui`, reexportados de
  `packages/ui`).
- `hooks/` — hooks genéricos (ex: debounce, media query, paginação) sem relação com um domínio.
- `lib/` — utilitários e o client HTTP base usado para falar com a API (`apps/api`).
- `types/` — tipos TypeScript genéricos compartilhados entre módulos.
