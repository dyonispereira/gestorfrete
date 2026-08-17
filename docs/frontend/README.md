# docs/frontend — Sprint 12 (Implementação do Frontend)

Índice da documentação técnica do Frontend real (`apps/web/`), contraparte executável de
[`docs/ux/`](../ux/) (decisões visuais) e [`docs/architecture/`](../architecture/) (DDD/Clean
Architecture, agora do lado do cliente). Onde os dois divergirem, o código que existe e roda vence
— mesmo princípio já usado em `docs/backend/README.md`.

Kickoff do usuário, na íntegra: Backend Freeze aprovado (D427/D428/D429, ver
[`../backend/BACKEND_FREEZE.md`](../backend/BACKEND_FREEZE.md)) → Sprint 12, começando por
**Lote 1 — Design System + Application Shell**, não por telas de Viagem. Ordem confirmada para o
resto do Frontend: Lote 1 (Design System + Shell) → Lote 2 (Auth + Tenant + Usuários + RBAC) →
Lote 3 (Cadastros) → Lote 4 (Frota) → Lote 5 (Operação/Viagens) → Manutenção → Financeiro → Fiscal
→ Tracking → Mobile/Admin → BI/IA.

## Lote 1 — Design System + Application Shell (concluído)

Fundação visual e técnica que todo lote seguinte reutiliza — nenhuma tela de negócio. O scaffold de
`apps/web/` (Fase 0) estava genuinamente vazio antes deste lote: Next.js/React/Tailwind/shadcn
configurados mas nada instalado (`pnpm-lock.yaml` inexistente), `packages/ui` era um
`export {}` literal, `core/auth`/`core/tenant`/`shared/*` só `.gitkeep`.

**Design tokens** (`packages/config/tailwind.preset.ts` + `apps/web/src/styles/globals.css`):
paleta deliberada — navy profundo (`--primary`) + âmbar (`--accent`) — para não ler como SaaS
genérico; a barra lateral usa seu próprio conjunto de tokens sempre-escuro (`--sidebar-*`),
independente do tema claro/escuro do conteúdo, âncora visual do ERP "premium" pedido pelo usuário.
Tipografia (Inter via `next/font/google`), espaçamento, grid (container `max-width: 1440px`),
raio de borda e sombras também tokenizados. Ícones: `lucide-react` (padrão shadcn/ui).

**Componentes base** (`packages/ui/`, consumidos via `@gestorfrete/ui`): Button, Input, Label,
Card, Avatar, Badge, Separator, Skeleton, ScrollArea, Tooltip, Dialog, DropdownMenu, Sheet,
Command (cmdk), Breadcrumb — padrão shadcn/ui (Radix primitives + `class-variance-authority` +
`tailwind-merge`), escritos à mão (não via CLI interativa, para já nascerem no pacote compartilhado
certo). Todos com `"use client"` — necessário porque Radix cria contexto React na avaliação do
módulo; sem isso, importar qualquer um deles a partir de um Server Component (`Sidebar`/`AppShell`)
quebra com `createContext is not a function` (bug real, encontrado e corrigido durante a verificação
em navegador deste lote).

**Fundação de Auth/Tenant/RBAC** (`apps/web/src/core/`), já ligada à API real, não a menus estáticos:

```
Login (POST /auth/login) → tokens (localStorage) → GET /auth/me → user + tenant + session
  → user.roles (UUIDs) → GET /roles/{id} por Papel → união de permission codes
  → NAV_GROUPS (universo de módulos, espelha RBAC_MATRIX.md §7.1–§7.29) filtrado pelos codes reais
  → Sidebar/Command autorizados
```

- `shared/lib/api-client.ts` — wrapper de `fetch` para `docs/api/openapi.yaml`: base
  `NEXT_PUBLIC_API_URL` + `/api/v1`, Bearer auth, refresh-and-retry único em `401` (requisições
  concorrentes compartilham o mesmo refresh em voo).
- `core/auth/auth-provider.tsx` — login/logout reais, token em `localStorage` (o contrato deixa o
  transporte do refresh token em aberto — "corpo ou cookie httpOnly, conforme a superfície" — e
  nunca decide para Web; cookie httpOnly exigiria o Backend emitir o cookie, que não existe hoje).
- `core/tenant/session-provider.tsx` — único dono de `GET /auth/me` (TanStack Query).
- `core/rbac/permissions-provider.tsx` + `nav-config.ts` + `use-authorized-nav.ts` — resolução de
  RBAC e o menu autorizado. `nav-config.ts` é estático só no sentido em que `RBAC_MATRIX.md` é
  estático (o universo de módulos não muda a cada request); o que renderiza é sempre computado a
  partir das permissões reais do usuário — nunca um menu por papel hardcoded.
- `core/tenant/branding.ts` — **achado real, não implementado**: `docs/api/002-tenants.md` adia
  explicitamente `GET/PATCH /tenant/settings/branding` ("fica para um lote futuro"); nem `Tenant`
  nem `TenantContext` têm campo de logo/cor. A Shell usa `Tenant.razao_social` (único campo real
  disponível) como nome exibido e cai no tema padrão (`--primary`) para cor/logo — nunca inventa
  valores por tenant. Vira decisão explícita quando/se `tenancy.visual_identity.edit` (código RBAC
  que já existe, sem endpoint correspondente) ganhar um lote de Backend.

**Shell** (`shared/components/shell/`): Sidebar (desktop, fixa) + MobileSidebar (Sheet, mesmo
conteúdo/tokens) + Header (breadcrumb + command/search + menu do usuário) + AppShell (composição).
Breadcrumb é derivado da rota + `nav-config` (nunca título por página escrito à mão). Command/Search
(⌘K / Ctrl K) busca só os itens que o usuário já pode ver — mesma fonte de RBAC do menu, não uma
lista separada. `RequireAuth` protege as rotas autenticadas no cliente (token em `localStorage` não
é legível por `middleware.ts`, que roda no edge/servidor).

**Rotas reais** (`apps/web/src/app/`): `/login`, `/dashboard` (dados reais de sessão — nome do
usuário, tenant — sem KPIs inventados, já que nenhum dado de negócio existe neste lote), `/m/[slug]`
(placeholder compartilhado para todo módulo autorizado-mas-ainda-não-construído — mostra
"módulo ainda não implementado", nunca uma tela CRUD fabricada). Estados de loading/empty/error são
componentes próprios (`shared/components/states/`), reaproveitados pelas páginas.

### Dois achados reais no Backend, encontrados testando o pipeline completo contra a API real

1. **CORS nunca esteve configurado** (`main.py`) — nenhum middleware de CORS existia porque, até
   este lote, nenhum navegador real jamais chamou a API (`curl`/servidor-a-servidor não são
   afetados por CORS, por isso passou despercebido durante todo o Backend). Sem isso, todo
   `fetch()` do navegador falharia silenciosamente antes da autenticação. Corrigido: `CORSMiddleware`
   + `Settings.cors_origins` (default `localhost:3000`/`3001`, os dois hosts de dev do Next.js).
   Rotina, sem ambiguidade de design — mesma classe dos dois bugs mecânicos corrigidos durante o
   Backend Freeze. Suíte completa (191 testes) e `ruff`/`mypy --strict` re-executados após a
   mudança — zero regressão, já que `create_app()` é usado por todo teste via `TestClient`/
   `AsyncClient`.
2. **`GET /auth/me` não cumpre a própria intenção documentada** — `001-authentication.md` já dizia
   que `user.roles` viria "expandido (nomes dos Papéis, não só IDs)... para montar a UI conforme
   RBAC, sem uma segunda chamada", mas a implementação real (`auth_schemas.py::MeResponse`) mantém
   `user.roles` como UUIDs e adiciona um campo `roles: list[string]` separado com só os *nomes* dos
   Papéis — não os *permission codes*. Nomes sozinhos não bastam para montar o menu autorizado; o
   Frontend deste lote resolve via `GET /roles/{id}` por Papel (funciona, testado ponta a ponta
   contra a API real). `openapi.yaml`/`001-authentication.md` atualizados para documentar o `roles`
   real (achado mecânico, corrigido na fonte). A lacuna de design em si — se `/auth/me` deveria
   devolver permission codes diretamente, cumprindo a intenção original — **não foi resolvida
   unilateralmente** (Backend congelado, D427/D428/D429): fica para decisão explícita no Lote 2 do
   Frontend (Auth + Tenant + Usuários + RBAC).

### Verificação

Testado ponta a ponta contra a API real (Postgres/Redis/RabbitMQ/MinIO portáteis, mesmos da Sprint
11): tenant + papel + usuário reais criados via `CreateRoleHandler`/`CreateUserHandler` (mesmo
padrão dos testes de integração, nunca dado fabricado direto no banco) com 14 permission codes
reais de `RBAC_MATRIX.md`; `POST /auth/login` → `GET /auth/me` → `GET /roles/{id}` confirmados via
chamada real, os 14 codes batendo exatamente com o Papel criado. `pnpm typecheck`/`pnpm lint`
limpos nos três pacotes (`@gestorfrete/types`, `@gestorfrete/ui`, `@gestorfrete/web`). Servidor de
desenvolvimento (`next dev`) rodado de verdade — `/login`, `/dashboard`, `/m/[slug]` retornam `200`
e renderizam os tokens/componentes corretos (confirmado inspecionando o HTML servido, já que este
ambiente não tem uma ferramenta de screenshot de navegador disponível).

## Como esta pasta cresce

Um lote por vez, mesmo princípio de `docs/backend/`. Próximo: **Lote 2 — Auth + Tenant + Usuários +
RBAC** (telas reais de login/recuperação de senha — depende da decisão sobre
`forgot-password`/`reset-password`, FALTANTE no Backend Freeze —, gestão de usuários/papéis).
