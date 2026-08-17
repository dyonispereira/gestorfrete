"""Componentes de negócio compartilhados entre múltiplos bounded contexts, sem RBAC/módulo próprio
(D354) — irmão de `core/` (infraestrutura técnica), `shared_kernel/` (building blocks de domínio
puros) e `modules/` (bounded contexts reais, D334/D335). Nunca um bounded context disfarçado: só
entra aqui o que nenhuma entrada de `RBAC_MATRIX.md` possui isoladamente.
"""
