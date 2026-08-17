# OBSERVABILITY.md — Logs, Request/Correlation ID, Health Checks

## Logging estruturado (`core/observability/logging.py`)

Todo log é uma linha JSON — nunca texto livre. `JsonFormatter` monta, por linha:

| Campo | Sempre presente? | Origem |
|---|---|---|
| `timestamp` | Sim | UTC, ISO 8601 |
| `level` / `logger` / `message` | Sim | `logging` padrão |
| `request_id` | Quando dentro de uma requisição HTTP | `core.observability.context` |
| `correlation_id` | Quando dentro de uma requisição HTTP | idem |
| `tenant_id` | Quando um Actor já foi resolvido (`get_current_actor`) | `core.multitenancy.context` |
| `user_id` | — | **Não populado automaticamente ainda** — nenhum código de negócio chama `logger.info(..., extra={"user_id": ...})` nesta etapa; o campo é suportado (qualquer `extra` vira chave no JSON), só não há chamador real até o Lote 2 |
| `exception` | Só em log de erro com `exc_info` | traceback formatado |
| qualquer `extra=` do call site | Sim | Copiado literalmente, exceto chaves sensíveis |

**Nunca dado sensível em log** — chaves como `password`/`senha`/`token`/`secret`/`authorization`/
`credential` em qualquer `extra` são substituídas por `"***REDACTED***"` automaticamente
(`_REDACTED_KEYS`), rede de segurança sobre a disciplina real (nunca passar segredo em `extra`).
Corpo de requisição/resposta nunca é logado (`RequestContextMiddleware` só loga método/path/status/
duração).

`configure_logging()` roda uma única vez, no início de `create_app()` — antes de qualquer outro
código do processo, para que `logging.getLogger(__name__)` funcione identicamente em qualquer
módulo. Nível controlado por `Settings.log_level`; o logger `sqlalchemy.engine` fica em `WARNING`
a menos que `debug=True` (evita inundar o log com SQL em produção).

## `request_id`/`correlation_id` (`core/observability/context.py` + `interfaces/middlewares/
request_context.py`)

- `request_id`: identifica **esta chamada HTTP específica** — sempre gerado novo a cada requisição,
  a menos que o cliente já envie `X-Request-Id` (propagação através de um proxy/gateway).
- `correlation_id`: identifica **uma cadeia de chamadas relacionadas** (ex.: um comando que dispara
  chamadas internas a outros serviços) — herda `X-Correlation-Id` do cliente quando presente, senão
  cai para o mesmo valor de `request_id` (a chamada é, por padrão, sua própria correlação raiz).

Ambos voltam como headers de resposta (`X-Request-Id`/`X-Correlation-Id`) e aparecem em todo
`ErrorEnvelope` (`ERROR_MODEL.md`) — suporte consegue localizar o log exato a partir do erro que o
usuário reportou, sem precisar de mais contexto.

## Health Checks (`interfaces/api/health.py`)

Fora de `/api/v1`, fora do contrato de negócio congelado (D332's exceção explícita para
infraestrutura):

| Rota | Verifica | Quando retorna erro |
|---|---|---|
| `GET /health` | Só que o processo responde | Nunca (sempre `200` se o processo está de pé) |
| `GET /health/live` | Nada externo — liveness Kubernetes-style | Nunca por dependência externa (evita crash-loop por um banco lento) |
| `GET /health/ready` | PostgreSQL + Redis + RabbitMQ + MinIO, um a um | `503` se qualquer um falhar, com `checks: {database, redis, rabbitmq, storage}` individualizado — nunca um booleano cego |

Cada `check_*_connection()` (`core.database.session`, `core.cache.redis_client`,
`core.messaging.rabbitmq_client`, `core.storage.minio_client`) retorna `bool`, nunca levanta —
testado explicitamente por não ter infraestrutura viva no ambiente onde este lote foi construído
(ver [`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md)): os quatro checks retornaram `False`
corretamente, sem vazar exceção, provando que o "modo de falha" funciona tão bem quanto o "modo de
sucesso" — algo que só testar o caminho feliz nunca prova.

## O que ainda não existe

Métricas (Prometheus/OpenTelemetry) e tracing distribuído — mencionados no pedido original como
"tempo de requisição" (já coberto, é `duration_ms` no log de acesso) mas não como um exportador de
métricas dedicado. Fica para quando o volume de bounded contexts justificar um dashboard
operacional real, não antecipado nesta fundação.
