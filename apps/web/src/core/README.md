# Core

Infraestrutura transversal do front-end — conceitos que atravessam todos os módulos de negócio.

## Estrutura

- `auth/` — fundação do contexto de autenticação (provider, hooks de sessão). Nesta etapa é apenas
  a estrutura; nenhuma tela ou fluxo de login foi implementado.
- `tenant/` — fundação do contexto multi-tenant no front-end: provider que expõe o tenant corrente
  para toda a árvore de componentes.
- `config/` — configuração de ambiente do front-end (variáveis públicas, feature flags).
