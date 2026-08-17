# APPLICATION_LAYER.md — `shared_kernel/application/`

Orquestra o Domain para realizar casos de uso — CQRS (`docs/architecture/cqrs.md`): escrita
(`Command`) e leitura (`Query`) nunca compartilham o mesmo canal de despacho, mesmo sendo tratados
de forma estruturalmente simétrica pela fundação.

## `Command`/`CommandHandler` (`command.py`) + `InMemoryCommandBus` (`command_bus.py`)

```python
@dataclass(frozen=True)
class CriarViagem(Command):
    cliente_id: uuid.UUID
    ...

class CriarViagemHandler(CommandHandler[CriarViagem, Viagem]):
    async def handle(self, command: CriarViagem) -> Viagem: ...
```

`InMemoryCommandBus.register(CommandType, handler)` — exatamente **um** handler por tipo de
Command (registrar um segundo para o mesmo tipo levanta
`CommandHandlerAlreadyRegisteredError`, testado); `dispatch()` levanta
`CommandHandlerNotRegisteredError` se nada foi registrado. Cada bounded context registra seus
próprios handlers no composition root (`main.py`) durante o startup — a fundação não sabe, e nunca
saberá, quais Commands existem.

## `Query`/`QueryHandler` (`query.py`) + `InMemoryQueryBus` (`query_bus.py`)

Espelha exatamente o mesmo padrão do CommandBus — classe separada de propósito (nunca reaproveitada
via herança comum), porque commands e queries são conceitualmente distintos em CQRS e misturar os
canais de despacho reabriria a possibilidade de uma Query "sujar" estado por engano. `QueryHandler`
pode, deliberadamente, ler direto da infraestrutura de persistência sem passar pelo Domain quando a
necessidade de apresentação for mais simples que remontar um Aggregate Root inteiro — Read Model
puro (`docs/api/019-trip-timeline.md`, `025-vehicle-availability.md`, etc. são o equivalente já
congelado no contrato HTTP).

## `EventBus` (porta, `event_bus.py`) e sua implementação (`core/messaging/event_bus.py`)

A porta é abstrata (`publish`/`subscribe`) — a implementação concreta
(`core.messaging.event_bus.RabbitMQEventBus`) publica em um único exchange topic `domain_events`,
routing key = nome da classe do evento. Detalhe completo em
[`EVENT_BUS.md`](./EVENT_BUS.md).

## Fluxo típico de um Command (padrão que todo módulo seguirá a partir do Lote 2)

```
Interfaces (router FastAPI)
      ↓ valida payload (Pydantic), monta o Command
Application (CommandHandler.handle)
      ↓ abre um SQLAlchemyUnitOfWork
      ↓ carrega o Aggregate Root via Repository (já filtrado por tenant, D208)
      ↓ chama o método de domínio que aplica a regra de negócio e grava o Domain Event
      ↓ repository.add(aggregate) — dentro da mesma sessão do UoW
      ↓ uow.commit() — persiste e, só então, publica os eventos gravados (TRANSACTION_MODEL.md)
      ↓ retorna o resultado (ou um Result[TValue, TError] quando a falha é uma regra de negócio esperada)
Interfaces
      ↓ serializa a resposta (schema Pydantic do módulo)
```

Nenhuma peça deste fluxo tem código de exemplo ainda em `modules/` — só os contratos genéricos
acima existem nesta etapa, testados isoladamente (`tests/unit/test_shared_kernel.py`).

## DTOs (`application/dtos/`, por módulo)

Cada módulo terá seus próprios DTOs de entrada/saída entre `application` e `interfaces` — nenhum
contrato genérico de DTO existe na fundação porque DTO é, por definição, específico do caso de uso.
A única regra transversal: um DTO nunca é o mesmo objeto que o schema Pydantic de
`interfaces/schemas/` (que conhece HTTP/OpenAPI) nem o mesmo que o modelo SQLAlchemy de
`infrastructure/persistence/models/` (que conhece a tabela física) — os três existem para
justamente permitir que HTTP, caso de uso e schema físico evoluam independentemente (D217 já
aplicado ao contrato OpenAPI: "Response nunca é cópia direta da tabela SQL").

## Como esta camada cresce

Primeiro handler real: `modules/identity_access/application/commands/` no Sprint 11 Lote 2,
implementando o primeiro comando de negócio (`Autenticar`/`CriarUsuario`) contra o Domain Model já
congelado de `docs/domain/001-cadastros.md`.
