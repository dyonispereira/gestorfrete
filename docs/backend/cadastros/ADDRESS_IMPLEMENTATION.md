# ADDRESS_IMPLEMENTATION.md — `Endereço` (componente compartilhado)

Contrato: [`../../api/011-addresses.md`](../../api/011-addresses.md). DDL:
[`../../database/relational/002-cadastros.md`](../../database/relational/002-cadastros.md) (`enderecos`).
RBAC: nenhuma — Endereço é autorizado pela permissão do dono (D216, ver `011-addresses.md`).

## Por que aqui, não em `crm`/`maintenance`

D354 — `Endereço` não tem bounded context próprio (nenhuma entrada RBAC). Implementado uma única
vez em `apps/api/src/shared/addresses/`, injetado por qualquer módulo dono. Ver
[`README.md`](./README.md#endereço-é-compartilhado-não-duplicado-d354).

## Domain

```
shared/addresses/domain/
├── value_objects/owner_type.py   # OwnerType(str, Enum): CLIENTE / FORNECEDOR / FILIAL
│                                   # (espelha enderecos_entidade_tipo_enum, D231)
├── value_objects/address_type.py # AddressType(str, Enum): PRINCIPAL / COBRANCA / ENTREGA / OUTRO
├── entities/address.py           # Address(BaseAggregateRoot[UUID]) — Não é sub-entidade de outro
│                                   # agregado Python (não existe um `Cliente.enderecos: list[...]`
│                                   # carregado em memória) porque `crm`/`maintenance` nunca
│                                   # importam `shared.addresses.domain` de volta para dentro do
│                                   # próprio agregado — cada endereço é seu próprio Aggregate Root
│                                   # tecnicamente, mesmo sendo "não-Aggregate-Root" no Domain Model
│                                   # de negócio (a fronteira transacional é por linha de endereço,
│                                   # nunca "salvar o Cliente inteiro com seus endereços").
└── repositories/address_repository.py  # AddressRepository(Repository[Address, UUID])
```

`Address.create(owner_type, owner_id, tipo, logradouro, numero, complemento, bairro, cidade, uf,
cep, audit)` — sem `id` de entidade-dona genérico solto: `owner_type`/`owner_id` sempre os dois
juntos, nunca um sem o outro (mesmo par que a coluna física `(entidade_tipo, entidade_id)`).

**Invariante que o Domain não pode garantir sozinho**: "no máximo um endereço `PRINCIPAL` vigente
por dono" é um índice único parcial físico (`uq_enderecos_entidade_principal`) — o
`SqlAlchemyAddressRepository.add()` deixa o Postgres rejeitar a segunda inserção (`IntegrityError`
→ `ConflictError("ADDRESS_PRINCIPAL_ALREADY_EXISTS")`), nunca uma checagem SELECT-then-INSERT em
Application (race condition real entre duas requisições concorrentes — a constraint física é a
única fonte de verdade aqui, não um "gentleman's agreement" da Application).

## Infrastructure

```
shared/addresses/infrastructure/persistence/
├── models/address_model.py            # AddressModel — tabela `enderecos`
└── repositories/sqlalchemy_address_repository.py
```

`SqlAlchemyAddressRepository` filtra por `owner_type` + `owner_id` (nunca só `owner_id` sozinho —
dois clientes de tenants diferentes nunca colidem porque `owner_id` já é escopado por
`tenant_id` na consulta, igual a todo outro Repository) + `tenant_id` do contexto corrente
(`core.multitenancy.context`, mesma disciplina D338/D339 de todo Repository deste projeto).

## Application

`CreateAddressCommand`/`UpdateAddressCommand`/`DeleteAddressCommand` +
`GetAddressQuery`/`ListAddressesQuery` — mesmo padrão Command/QueryHandler de todo o resto do
projeto (não "funções livres" — consistência com o restante do código venceu a ideia original mais
minimalista), cada um recebendo `owner_type`/`owner_id` explícitos. `CreateAddressHandler`/
`UpdateAddressHandler` nunca fazem `SELECT`-then-`INSERT` para checar o endereço `PRINCIPAL`
duplicado — deixam o índice único parcial físico rejeitar via `IntegrityError`, convertido em
`ConflictError("ADDRESS_PRINCIPAL_ALREADY_EXISTS")` (evita a janela de corrida de duas requisições
concorrentes). Não existe um "AddressService" agindo como segunda fonte de autorização — a
permissão já foi checada pelo router do dono (`require_permission("crm.client.edit")`, etc.) antes
de qualquer Command/Query de Endereço rodar (D341).

`interfaces/schemas/address_schemas.py` — `AddressResponse`/`CreateAddressRequest`/
`UpdateAddressRequest` também vivem em `shared/addresses/`, reusados por `crm`/`maintenance`
(o recurso é idêntico por contrato — schema HTTP duplicado não teria nenhum benefício de
isolamento entre bounded contexts, só manutenção dobrada).

## Como cada módulo dono usa isto

```python
# modules/crm/interfaces/api/client_router.py
from shared.addresses.application.commands.create_address import CreateAddressCommand, CreateAddressHandler
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared.addresses.interfaces.schemas.address_schemas import AddressResponse, CreateAddressRequest

@router.post("/{client_id}/addresses", response_model=AddressResponse, status_code=201)
async def create_client_address(
    client_id: uuid.UUID, body: CreateAddressRequest,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.edit")),
):
    await GetClientHandler(...).handle(...)  # 404 se o Cliente não existir
    dto = await CreateAddressHandler().handle(
        CreateAddressCommand(actor=actor, owner_type=OwnerType.CLIENTE, owner_id=client_id, ...)
    )
    return AddressResponse.from_dto(dto)
```

`owner_type` é sempre fixado pelo router do dono (nunca um campo que o cliente da API escolhe,
D227/D208 aplicado a uma associação de domínio) — exatamente o path `/clients/{id}/addresses` já
implica `OwnerType.CLIENTE`.

## Verificação de que o dono existe antes de criar/listar endereços

`POST/GET /{owner}/{id}/addresses` retorna `404` se o dono não existir (`011-addresses.md`) — cada
router do dono já resolve o dono via seu próprio Repository (`ClientRepository.get_by_id`) antes de
chamar o serviço de Endereço; `shared/addresses` nunca precisa saber como validar um Cliente/
Fornecedor, só recebe um `owner_id` já confirmado como existente.

## `import-linter`

Novo contrato: `shared` nunca importa `modules`/`interfaces` (mesma forma do contrato já existente
para `core`). `modules.crm`/`modules.maintenance` podem importar `shared.addresses` livremente
(é infraestrutura compartilhada, não um bounded context de outro módulo).

## Testes (D352)

- Unit: `Address.create()` valida VOs (`OwnerType`/`AddressType`).
- Integration: `SqlAlchemyAddressRepository` contra Postgres real — cria endereço para um Cliente,
  confirma isolamento por tenant, confirma que um segundo `PRINCIPAL` para o mesmo dono levanta
  `ConflictError` (prova a constraint física, não assumida).
- E2E: `POST /clients/{id}/addresses` → `GET /clients/{id}/addresses` → `PATCH` → `DELETE` (soft
  delete) via HTTP real, coberto dentro de `CLIENT_IMPLEMENTATION.md`'s test suite (reusa a mesma
  suíte — não duplicado para `suppliers`, já que o comportamento é idêntico por contrato).
