# CI_PIPELINE.md — Barreira mínima antes de qualquer deploy

V1 Operational Hardening — item de INFRA pedido explicitamente pelo usuário: "não precisa criar
uma plataforma DevOps complexa. Quero somente a barreira mínima de segurança para impedir deploy
de build quebrada." Não existia nenhum workflow de CI antes deste documento (`.github/workflows/`
vazio) — todo o deploy era manual, sem nenhuma verificação automática interposta, P0 registrado no
Go-Live Audit. **Pilot Hardening Final, Parte 2**: fechado —
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) existe de verdade e roda exatamente os
comandos já usados manualmente durante todo este projeto para verificar cada rodada de trabalho —
nenhum comando novo, nenhuma ferramenta nova.

**Correção sobre a versão anterior deste documento**: o rascunho original desta página listava
`pytest tests/unit tests/integration -q` e `pytest tests/ -m integration -q` na tabela, mas o
esboço de YAML só incluía o segundo comando — inconsistência resolvida no workflow real com dois
passos separados (`pytest -q` para a suíte unit via o marcador padrão `-m 'not integration'`, depois
`pytest -m integration -q`), cada um aparecendo com seu próprio resultado no log do CI. O esboço
original também só declarava serviços de `postgres`/`redis` no job `backend`, mas o marcador
`integration` do `pytest.ini_options` já documentava depender de `rabbitmq`/`minio` também
(`test_infrastructure_connectivity.py` testa isso diretamente) — o workflow real inclui `rabbitmq`
como serviço e sobe o MinIO via `docker run` manual (o bloco `services:` do GitHub Actions não
aceita um comando customizado como o `server /data` que a imagem `minio/minio` exige).

## O que o pipeline verifica (backend, `apps/api/`)

| Passo | Comando | Falha o build se |
|---|---|---|
| Lint | `poetry run ruff check .` | Qualquer violação de estilo/import não resolvida |
| Tipos | `poetry run mypy src` | Qualquer erro de tipo — as 7 exceções pré-existentes de stub ausente `jose`/`passlib` foram fechadas de verdade na Parte 3 deste mesmo lote (`types-passlib`/`types-python-jose` como dev deps reais), não com `# type: ignore`; `mypy src` está genuinamente zero-erro hoje |
| Fronteiras de módulo | `PYTHONPATH=src poetry run lint-imports` | Qualquer contrato de `import-linter` quebrado (D090/D149/D161/D285/D421/D426, `DEPENDENCY_RULES.md`) |
| Migrations aplicam limpo | `poetry run alembic upgrade head` contra um Postgres efêmero (serviço do próprio job de CI, não o banco de desenvolvimento) | Qualquer migration que não aplique em banco vazio |
| Testes (unit) | `poetry run pytest -q` (marcador padrão `-m 'not integration'`) | Qualquer teste vermelho |
| Testes (integration) | `poetry run pytest -m integration -q` contra Postgres/Redis/RabbitMQ efêmeros + MinIO via `docker run` | Qualquer teste vermelho |

## O que o pipeline verifica (frontend, `apps/web/` + `packages/*`)

| Passo | Comando | Falha o build se |
|---|---|---|
| Tipos | `pnpm typecheck` (roda em todos os workspaces via Turbo) | Qualquer erro de TypeScript |
| Lint | `pnpm lint` (`next lint`) | Qualquer warning/erro do ESLint |
| Build | `pnpm build` | Build de produção do Next.js falhar |

## E2E (`apps/web/e2e/`)

```bash
docker compose -f infra/compose/docker-compose.yml --env-file infra/compose/.env.example up -d
docker compose -f infra/compose/docker-compose.yml exec -T api poetry run alembic upgrade head
npx playwright test  # workers: 1, sequencial — mesma configuração já usada localmente
```

Roda contra a stack completa via `docker-compose.yml` (mesmo ambiente usado manualmente durante
todo este projeto), não um mock — é a suíte que mais realisticamente reproduz produção,
propositalmente mais lenta e rodando por último, depois que os passos rápidos acima já filtraram a
maioria dos problemas.

## Workflow real (`.github/workflows/ci.yml`)

O arquivo real está em [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — não
duplicado aqui para não haver duas fontes de verdade divergentes (esta seção é só a explicação de
alto nível; qualquer mudança de comando/versão deve ser feita no workflow, este texto só
acompanha).

Três jobs, `backend`/`frontend` em paralelo, `e2e` só depois dos dois passarem (a barreira cara
roda por último, nunca bloqueia feedback rápido de lint/tipo). Branch protection em `main` exige os
três jobs verdes antes de merge — esse é o mecanismo real de "impedir deploy de build quebrada"
pedido pelo usuário; nenhum passo de deploy automático está incluído aqui (fora de escopo
explícito, "não precisa criar uma plataforma DevOps complexa").

## Health checks pós-deploy (já existentes, só referenciados aqui)

`/health/live` (liveness — processo responde) e `/health/ready` (readiness — Postgres + Redis
alcançáveis, `check_database_connection`/`check_redis_connection`) já existem e são bem desenhados
(`OBSERVABILITY.md`). O pipeline acima não os chama diretamente (não há passo de deploy real
ainda), mas qualquer mecanismo de deploy futuro deve gatear o cutover de tráfego em
`/health/ready`, nunca só em "o processo subiu".

## Fora de escopo desta rodada (não esquecido)

- Deploy automático (CD) — só a barreira de CI (build quebrada nunca chega a `main`), sem o próximo
  passo de promover automaticamente para produção.
- Cache de dependências entre execuções do CI (acelera, não muda o que é verificado) — otimização,
  não correção.
- Notificação de falha (Slack/e-mail) — GitHub já notifica por padrão via PR status checks;
  integração adicional fica para quando houver necessidade real.
