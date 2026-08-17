# INFRASTRUCTURE_LAYER.md — `core/` + `shared_kernel/infrastructure/`

A única camada que sabe qual banco, fila, cache e storage o sistema usa de fato — implementa os
contratos que `domain`/`application` declaram, nunca o contrário (`docs/architecture/
clean-architecture.md`). Tudo neste documento existe de verdade em `apps/api/src/`, testado.

## `core/config` — `Settings` (`settings.py`)

`pydantic-settings`, única fonte de variáveis de ambiente do processo — **nenhum módulo lê
`os.environ`/`os.getenv` diretamente em nenhum outro arquivo** (verificável por `grep -r
"os.environ\|os.getenv" src/ --include=*.py | grep -v config/settings.py`, hoje zero resultados).

| Campo | Tipo | Observação |
|---|---|---|
| `environment` | `Literal["local","test","staging","production"]` | Nunca uma string livre — erro de digitação vira erro de validação no boot, não um bug silencioso em produção |
| `log_level` | `Literal["DEBUG",...,"CRITICAL"]` | Consultado por `core.observability.logging.configure_logging` |
| `database_url`/`database_pool_size`/`database_max_overflow`/`database_pool_timeout_seconds` | | Pool explícito, não os defaults do SQLAlchemy |
| `redis_url` / `rabbitmq_url` | | |
| `minio_endpoint`/`minio_access_key`/`minio_secret_key`/`minio_secure` | | |
| `jwt_secret_key`/`jwt_algorithm`/`jwt_access_token_expire_minutes` | | Fundação apenas — sem fluxo de login ainda (Lote 2) |

`get_settings()` é `@lru_cache` — uma única instância por processo, recarregada só se o processo
reiniciar (comportamento padrão de todo projeto FastAPI+pydantic-settings).

## `core/database` — conexão, sessão, Unit of Work, health check

- `session.py`: `get_engine()` (pool configurado via `Settings`, `pool_pre_ping=True`),
  `get_session_factory()`, `get_session()` (dependency FastAPI, gera uma `AsyncSession` por
  requisição), `check_database_connection()` (`SELECT 1`, nunca levanta — retorna `bool`, usado por
  `/health/ready`), `dispose_engine()` (chamado no `lifespan` de shutdown).
- `unit_of_work.py`: `SQLAlchemyUnitOfWork` — implementação concreta de
  `shared_kernel.infrastructure.unit_of_work.UnitOfWork`. Uma instância por Command tratado (nunca
  reaproveitada entre requisições); `commit()`/`rollback()` delegam à `AsyncSession` interna;
  `__aexit__` sempre fecha a sessão, mesmo em erro. Detalhe completo em
  [`TRANSACTION_MODEL.md`](./TRANSACTION_MODEL.md).

**Nenhum modelo ORM existe ainda** — `alembic/env.py` continua com `target_metadata = None`, D-mesmo
princípio já documentado ali desde a Fase 0: o primeiro `Base.metadata` combinado só é atribuído
quando o primeiro bounded context declarar `infrastructure/persistence/models/` de verdade
(Sprint 11 Lote 2).

## `core/cache` — Redis (`redis_client.py`)

`get_redis_client()` (`@lru_cache`) + `check_redis_connection()` (`PING`, nunca levanta).

## `core/messaging` — RabbitMQ (`rabbitmq_client.py`, `event_bus.py`)

`get_rabbitmq_connection()` (conexão robusta única por processo, reconecta sozinha via
`aio_pika.connect_robust`), `close_rabbitmq_connection()`, `check_rabbitmq_connection()`. A
implementação do `EventBus` (`RabbitMQEventBus`) mora aqui — detalhe completo em
[`EVENT_BUS.md`](./EVENT_BUS.md).

## `core/storage` — MinIO (`minio_client.py`)

`get_minio_client()` + `check_storage_connection()` — o SDK `minio` é síncrono; o health check usa
`asyncio.to_thread` para não bloquear o event loop (única chamada de I/O síncrona em todo `core/`,
deliberadamente isolada). Nenhum bucket é criado aqui — pertence à `infrastructure` do bounded
context `storage` quando `078-storage.md`/`079-files.md` (D314/D315/D324) forem implementados.

## `core/security` — JWT e senha

- `ports.py` (já existia, Fase 0): `PasswordHasher`/`TokenService`, `Protocol`s puros.
- `jwt_token_service.py`: `JWTTokenService` (implementação concreta via `python-jose`) —
  `issue_access_token(subject, claims)`/`decode_access_token(token)`; levanta `TokenExpiredError`/
  `InvalidTokenError` (nunca a exceção crua do `jose`, mesmo princípio de `core.exceptions` nunca
  vazar detalhe de biblioteca externa).
- `password_hasher.py`: `BcryptPasswordHasher` (via `passlib[bcrypt]`) — ver a nota de compatibilidade
  de versão em [`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md).

## `core/multitenancy` — `context.py`

`ContextVar` de `tenant_id` corrente (já existia, Fase 0) — `set_current_tenant_id`/
`get_current_tenant_id`/`reset_current_tenant_id`; `get_current_tenant_id()` levanta
`TenantNotSetError` se nada foi resolvido ainda, nunca retorna um tenant "vazio"/`None` silencioso.
Populado por `interfaces.dependencies.auth.get_current_actor` a cada requisição autenticada — ver
[`INTERFACES_LAYER.md`](./INTERFACES_LAYER.md).

## `core/observability` — logging estruturado + contexto de requisição

- `context.py`: `ContextVar`s de `request_id`/`correlation_id` (mesmo padrão de `multitenancy`).
- `logging.py`: `JsonFormatter` — todo log é uma linha JSON (`timestamp`/`level`/`logger`/`message`
  + `request_id`/`correlation_id`/`tenant_id` quando disponíveis + qualquer `extra` do call site).
  Chaves sensíveis (`password`, `senha`, `token`, `secret`, `authorization`, ...) são
  automaticamente substituídas por `***REDACTED***` se aparecerem em `extra` — rede de segurança,
  nunca a única linha de defesa (a disciplina real é simplesmente nunca colocar segredo em `extra`).
  Detalhe completo em [`OBSERVABILITY.md`](./OBSERVABILITY.md).

## `core/exceptions` — hierarquia + handlers

`base.py` (hierarquia) + `envelope.py` (schemas Pydantic do envelope) + `handlers.py` (registro
FastAPI). Detalhe completo em [`ERROR_HANDLING.md`](./ERROR_HANDLING.md).

## O que ainda não existe

`infrastructure/persistence/models/` e `infrastructure/persistence/repositories/` de qualquer
bounded context — pedido explícito do usuário para este lote ("Não criar ainda os models das 133+
tabelas"). `infrastructure/messaging/` de cada módulo (publishers/consumers específicos) também
vazio — só a base RabbitMQ transversal existe.
