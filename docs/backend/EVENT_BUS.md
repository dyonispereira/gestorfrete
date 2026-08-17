# EVENT_BUS.md — Barramento de Eventos (RabbitMQ)

## Porta vs. implementação

`shared_kernel.application.event_bus.EventBus` (porta, já existia na Fase 0) declara `publish`/
`subscribe`, genéricos sobre `DomainEvent`. `core.messaging.event_bus.RabbitMQEventBus` (novo neste
lote) é a única implementação concreta — nenhum bounded context deveria importar `aio_pika`
diretamente, sempre a porta.

## Topologia — um único exchange, routing key = nome do evento

```python
EXCHANGE_NAME = "domain_events"   # topic exchange, durável
```

Todo evento de domínio de qualquer bounded context passa por este único exchange — a routing key é
sempre `type(event).__name__` (`"ViagemCriada"`, `"WebhookFalhou"`, ...), o mesmo nome exato
catalogado em `docs/product/EVENT_MAP.md` (D032 — publicadores nunca sabem quem consome; quem
decide o roteamento é o binding da fila no RabbitMQ, não código Python). Um exchange único (em vez
de um por bounded context) mantém a topologia simples nesta fundação — se o volume um dia justificar
exchanges por domínio, é uma migração de infraestrutura, não uma mudança de contrato de evento.

## Serialização

`serialize_event(event)` — `dataclasses.asdict(event)` + `event_type` (nome da classe) + `json.dumps`
com um `default` que sabe converter `UUID`/`datetime`/`date` para string (ISO 8601). Nenhum bounded
context escreve sua própria serialização — todo `DomainEvent` concreto, sendo um `@dataclass`, já
serializa corretamente por essa função genérica.

## `publish` — requer `connect()` primeiro

```python
bus = RabbitMQEventBus()
await bus.connect()          # declara o exchange, abre o channel
await bus.publish(evento)     # RuntimeError se connect() não rodou ainda
```

`connect()` é idempotente-por-instância (uma vez por processo, tipicamente no `lifespan` de startup
quando o primeiro bounded context precisar publicar — ainda não chamado em lugar nenhum, porque
nenhum evento de domínio real existe nesta etapa de fundação).

## `subscribe` — só registra, não consome ainda

```python
bus.subscribe(ViagemCriada, meu_handler)
```

Registra o handler num dicionário em memória (`dict[type[DomainEvent], list[EventHandler]]`).
**Não** declara fila nem começa a consumir — isso é responsabilidade de um método
`start_consuming()` que só faz sentido depois que **todos** os bounded contexts já registraram seus
handlers no boot (ordem importa: registrar depois de começar a consumir perderia mensagens já
roteadas). Como nenhum handler de evento de negócio existe ainda, `start_consuming()` não foi
implementado nesta etapa — construí-lo agora seria código morto sem nada real para exercitá-lo;
entra no primeiro lote que precisar de um consumidor de fato (ex.: `notification_center` reagindo a
eventos de outros módulos, `086-notifications.md`).

## `close`

Fecha a conexão robusta subjacente — chamado do `lifespan` de shutdown quando o event bus estiver
de fato em uso (hoje, `close_rabbitmq_connection()` em `core.messaging.rabbitmq_client` já cobre a
conexão crua; `RabbitMQEventBus.close()` existe para quando a instância do bus for gerenciada
separadamente da conexão bruta).

## Verificação nesta etapa

Sem RabbitMQ disponível no ambiente de sandbox usado para este lote (ver
[`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md)), `connect()`/`publish()`/`subscribe()` não foram
exercitados contra um broker real — a lógica de serialização/roteamento foi revisada por leitura e
por `mypy --strict`, mas a prova de conectividade real fica para quando o usuário rodar `docker
compose up` e `pytest -m integration` localmente (`check_rabbitmq_connection()` já cobre a
conectividade crua; publicar/consumir um evento de fato só terá um teste de integração quando
existir um evento de domínio real para testar).
