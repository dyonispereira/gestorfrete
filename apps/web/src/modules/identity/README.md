# Identity

Módulo de front-end responsável pela experiência de usuários, papéis e permissões (RBAC). Espelha o bounded context `identity_access` do backend. Nesta etapa é apenas estrutura — sem tela de login.

## Estrutura

- `components/` — componentes React específicos deste módulo (ainda não implementados nesta etapa de fundação).
- `hooks/` — hooks de estado e side-effects específicos deste módulo.
- `services/` — chamadas à API do backend (via `shared/lib`), isoladas por módulo.
- `types/` — tipos TypeScript específicos deste módulo.
