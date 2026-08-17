# TRANSACTION_MODEL.md — Fronteiras de Transação e Conexão

## Unit of Work — uma transação por Command

`core.database.unit_of_work.SQLAlchemyUnitOfWork` implementa
`shared_kernel.infrastructure.unit_of_work.UnitOfWork` (contrato já existente desde a Fase 0). Uma
instância nova por Command tratado — nunca reaproveitada entre requisições, nunca compartilhada
entre dois Commands:

```python
async with SQLAlchemyUnitOfWork() as uow:
    repo = SomeConcreteRepository(uow.session)
    aggregate = await repo.get_by_id(id)
    aggregate.do_something()          # grava Domain Events internamente (record_event)
    await repo.add(aggregate)
# __aexit__: sem exceção → commit(); com exceção → rollback() — sempre, e sempre fecha a sessão
```

`__aenter__`/`__aexit__` (herdados da base abstrata) decidem commit vs. rollback automaticamente
pela presença de exceção — nenhum código de aplicação escreve `try/except` manual para isso.

## Eventos só são publicados **depois** do commit, nunca antes

Ordem não-negociável, já implícita no desenho de `BaseAggregateRoot.pull_domain_events()` +
`UnitOfWork`:

```
1. Aggregate.record_event(...)     — evento gravado em memória, nada persistido ainda
2. repository.add(aggregate)        — SQLAlchemy adiciona à sessão, ainda não commitado
3. uow.commit()                      — COMMIT real no PostgreSQL
4. handler.pull_domain_events()       — só agora os eventos são retirados do agregado
5. event_bus.publish(evento) por evento — só agora vão para o RabbitMQ
```

Publicar antes do passo 3 arriscaria outro bounded context reagir a um evento cuja transação de
origem ainda pode dar rollback — inconsistência que nenhuma quantidade de retry no consumidor
resolveria depois. O `CommandHandler` concreto (ainda não escrito — Lote 2) é responsável por essa
sequência; a fundação só garante que `commit()` e `pull_domain_events()` são operações distintas e
ordenáveis pelo chamador, nunca uma acontecendo como efeito colateral automático da outra.

## Conexões — lazy, nunca eager no startup

`main.py`'s `lifespan` **não** conecta a Postgres/Redis/RabbitMQ/MinIO no boot — `get_engine()`
(SQLAlchemy `pool_pre_ping=True`), `get_redis_client()`, `get_rabbitmq_connection()`,
`get_minio_client()` são todos `@lru_cache`/lazy, conectando de fato só no primeiro uso real
(inclusive a primeira chamada de `/health/ready`). Decisão deliberada: uma dependência que demora
alguns segundos a mais para ficar pronta não pode derrubar o processo inteiro em crash loop —
`docker-compose.yml`'s `depends_on: condition: service_healthy` já sequencia a ordem de subida dos
containers; `/health/ready` é a prova de conectividade real, não o boot do processo.

`dispose_engine()`/`close_rabbitmq_connection()` são chamados no `lifespan` de shutdown — conexões
pooled são liberadas explicitamente, nunca abandonadas para o SO limpar.

## Pool de conexões — configurável, nunca hardcoded

`Settings.database_pool_size` (default 5) / `database_max_overflow` (default 10) /
`database_pool_timeout_seconds` (default 30) — os três repassados literalmente para
`create_async_engine`. Ajustar o tamanho do pool em produção é mudança de variável de ambiente,
nunca de código.

## O que ainda não existe

Nenhuma transação distribuída/2PC entre bounded contexts — cada Command altera exatamente um
Aggregate Root de um bounded context; consistência entre bounded contexts é sempre eventual, via
evento (Event-Driven, `docs/architecture/event-driven.md`), nunca uma transação única cobrindo duas
tabelas de dois módulos diferentes.
