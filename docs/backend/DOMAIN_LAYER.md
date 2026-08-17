# DOMAIN_LAYER.md — `shared_kernel/domain/`

A camada mais interna (`docs/architecture/clean-architecture.md`) — Python puro, zero import de
FastAPI/SQLAlchemy/nenhuma biblioteca de infraestrutura. Verificado mecanicamente, não só
declarado: `import-linter` (`pyproject.toml`, contrato "Shared Kernel never imports core, modules or
interfaces") falha o build se qualquer arquivo aqui importar algo fora de `shared_kernel.domain`.

Cada bounded context terá seu próprio `modules/<contexto>/domain/{entities,value_objects,events,
repositories}/` a partir do Lote 2 — nada ali existe ainda (D101-style: nenhuma entidade concreta é
criada sem um Domain Model já congelado a traduzir, e a tradução de Viagem/Cliente/etc. é trabalho
de bounded context, não de fundação).

## `BaseEntity[TId]` (`base_entity.py`)

Identidade, não valor: dois `BaseEntity` são iguais quando `id` é igual, independente dos demais
atributos — e nunca iguais a uma instância de outro tipo mesmo com o mesmo `id` (testado
explicitamente, `tests/unit/test_shared_kernel.py::TestBaseEntity`).

## `BaseAggregateRoot[TId]` (`base_aggregate_root.py`)

Estende `BaseEntity` com `record_event()`/`pull_domain_events()` — todo evento de domínio nasce
gravado no agregado que o originou, nunca publicado diretamente; a Application layer os retira
(`pull_domain_events()`, que também limpa a lista) depois que o `UnitOfWork` confirma a transação,
nunca antes (ver [`TRANSACTION_MODEL.md`](./TRANSACTION_MODEL.md)).

## `BaseValueObject` (`base_value_object.py`)

Marcador — sem identidade, igualdade por atributo. Concretizações usam `@dataclass(frozen=True)`,
que já dá `__eq__`/imutabilidade de graça; a classe base só existe para tipagem/documentação de
intenção (`isinstance(x, BaseValueObject)` continua útil em type guards).

## `DomainEvent` (`domain_event.py`)

```python
@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    event_id: uuid.UUID
    occurred_at: datetime
    tenant_id: uuid.UUID | None
```

Fato imutável já ocorrido — nunca uma intenção (isso é `Command`, ver
[`APPLICATION_LAYER.md`](./APPLICATION_LAYER.md)). Todo evento concreto (`ViagemCriada`,
`WebhookFalhou`, ...) estende esta base e adiciona seus próprios campos — o nome da subclasse
**é** o nome que aparece em `docs/product/EVENT_MAP.md` e a routing key usada por
`core.messaging.event_bus.RabbitMQEventBus` (serialização automática via
`dataclasses.asdict` + `type(event).__name__`, nenhum mapeamento manual).

## `Result[TValue, TError]` (`result.py`)

Either/Result pattern — usado por operações de domínio/aplicação que podem falhar de forma
*esperada* (regra de negócio violada), como alternativa a levantar exceção quando o chamador precisa
decidir o que fazer sem uma try/except. `.value`/`.error` levantam `ValueError` se acessados no lado
errado (`is_success`/`is_failure` sempre checados primeiro) — testado em
`tests/unit/test_shared_kernel.py::TestResult`.

## `Specification[TCandidate]` (`specification.py`)

Regra de negócio como objeto, combinável com `&`/`|`/`~` (AND/OR/NOT — testado explicitamente).
Cada módulo declara suas próprias especificações concretas (ex.: `ViagemAtrasadaSpecification`);
uma especificação com ciência de persistência (traduzindo para `WHERE` SQL) é responsabilidade da
`infrastructure/persistence` daquele módulo, nunca desta classe base.

## `Repository[TAggregate, TId]` (`repository.py`)

Port do Repository Pattern — `get_by_id`/`add`/`find(Specification)`. Dois princípios não
negociáveis, ambos já impostos pela assinatura do método, não só por convenção:

1. **Um repositório por Aggregate Root, nunca por entidade interna** (D237) — não existe
   `ItemRepository` para um item que só existe dentro do agregado Ordem de Serviço, por exemplo.
2. **Nenhum método recebe `tenant_id`** — a implementação concreta lê
   `core.multitenancy.context.get_current_tenant_id()` internamente; nenhum chamador em nenhuma
   camada pode "esquecer" de filtrar por tenant, porque a assinatura do método não dá espaço para
   informar um tenant diferente do que já está no contexto da requisição (D208 aplicado até a
   camada de persistência).

## `AuthenticatedActor` (`actor.py`)

```python
@dataclass(frozen=True)
class AuthenticatedActor:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
```

Quem está fazendo a requisição atual — resolvido uma única vez por
`interfaces.dependencies.auth.get_current_actor` (ver [`INTERFACES_LAYER.md`](./INTERFACES_LAYER.md))
e passado explicitamente para handlers de Command/Query que precisem saber o ator, nunca redescoberto
a partir de variável global em outro ponto do código.

## O que ainda não existe (deliberadamente)

Nenhuma Entidade/Value Object/Domain Event concreto de nenhum bounded context — `Viagem`,
`Cliente`, `Motorista` etc. só nascem quando o Lote correspondente do Backend traduzir
`docs/domain/`/`docs/database/dictionary/` para código, exatamente como cada `relational/NNN.md`
traduziu o Dictionary para SQL no Sprint 09. Escrever qualquer entidade de negócio agora seria
inventar sem uma tradução completa por trás — mesma disciplina de D101 aplicada ao código.
