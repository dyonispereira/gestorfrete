# CLIENT_IMPLEMENTATION.md — `Cliente`, `Contato do Cliente` (`modules/crm/`)

Contrato: [`../../api/007-clients.md`](../../api/007-clients.md),
[`../../api/012-contacts.md`](../../api/012-contacts.md),
[`../../api/011-addresses.md`](../../api/011-addresses.md) (sub-recurso).
DDL: [`../../database/relational/002-cadastros.md`](../../database/relational/002-cadastros.md)
(`clientes`, `contatos_cliente`). RBAC: `crm.client.*`, `crm.client_contact.*`
(`RBAC_MATRIX.md` §7.1).

## Domain

```
modules/crm/domain/
├── value_objects/client_status.py   # ClientStatus: ATIVO / INATIVO
├── entities/client.py               # Client(BaseAggregateRoot[UUID]) — raiz; ContatoCliente é filho
├── entities/client_contact.py       # ClientContact(BaseEntity[UUID]) — não-Aggregate-Root
└── repositories/
    ├── client_repository.py         # get_by_id, exists_with_document, list_page, add
    └── client_contact_repository.py # get_by_id, list_for_client, add
```

`Client.create(codigo, razao_social, nome_fantasia, document, telefone, email, audit)`.
`Client.update(...)`, `Client.deactivate(deactivated_by, now)` (soft delete, D343). `document`
aceita CNPJ ou CPF (`cnpj_cpf` física) — validação de formato fica fora de escopo deste lote (o
contrato só diz `type: string`, nenhum VO de CNPJ/CPF com dígito verificador ainda existe no
projeto; **não** inventado aqui, D216-like disciplina aplicada a validação, não só a RBAC).

`ClientContact` é criado/atualizado/excluído via métodos no próprio agregado `Client`
(`add_contact`, `update_contact`, `remove_contact` operando sobre uma lista carregada) **ou** via
Repository dedicado direto (`ClientContactRepository`) — decisão: **Repository dedicado**, não
list-in-memory no agregado `Client`, porque `contatos_cliente` já tem seu próprio ciclo de vida via
RBAC (`crm.client_contact.*`, permissões distintas de `crm.client.*`) e endpoints HTTP próprios
(`/clients/{id}/contacts`) — carregar todos os contatos toda vez que o Cliente é lido seria
desperdício sem benefício de consistência transacional real (nenhuma regra cruza Cliente+Contato
numa única invariante). Mesmo raciocínio já usado para Endereço (D354) aplicado aqui a um caso
menos extremo — `ClientContact` continua sendo parte do agregado *no Domain Model* (nunca ganha
RBAC/rota fora de `/clients/{id}/...`), só não é carregado em memória via o objeto Python `Client`.

## Infrastructure

```
modules/crm/infrastructure/persistence/
├── models/client_model.py           # ClientModel — tabela `clientes`
├── models/client_contact_model.py   # ClientContactModel — tabela `contatos_cliente`
└── repositories/
    ├── sqlalchemy_client_repository.py
    └── sqlalchemy_client_contact_repository.py
```

Ambos filtram por `tenant_id` do contexto corrente (D338/D339); `ClientContactRepository` também
filtra por `cliente_id` explícito em `list_for_client` (nunca lista contatos de outro Cliente).

## Application

`CreateClientCommand`/`UpdateClientCommand`/`DeactivateClientCommand` +
`GetClientQuery`/`ListClientsQuery` — mesmo padrão UoW-por-Command do Lote 2
(`CommandHandler` constrói seu próprio `SQLAlchemyUnitOfWork`, nunca `session.commit()` dentro do
Repository, D342). Cada Command crítico (create/deactivate) grava `logs_auditoria` via
`AuditLogger.record(...)` na mesma transação (D344), reusando `core.audit` sem nenhuma
implementação paralela.

`CreateClientContactCommand`/`UpdateClientContactCommand`/`DeleteClientContactCommand` +
`ListClientContactsQuery` — mais simples, sem auditoria própria (`contatos_cliente` não tem
`criado_por`/`atualizado_por` na DDL, D217 já documentado em `012-contacts.md`: a tabela reflete
exatamente o que existe, nunca inventa um campo).

Endereço: `CreateClientAddressCommand`/etc. delegam para `shared.addresses.application` com
`owner_type=OwnerType.CLIENTE`, `owner_id=client_id` — ver
[`ADDRESS_IMPLEMENTATION.md`](./ADDRESS_IMPLEMENTATION.md). O router de `crm` primeiro confirma que
o Cliente existe (`ClientRepository.get_by_id`, `404` se não) antes de chamar o serviço
compartilhado.

## Interfaces

`interfaces/api/client_router.py` — `GET/POST /clients`, `GET/PATCH/DELETE /clients/{id}`,
`GET/POST /clients/{id}/addresses`, `GET/PATCH/DELETE /clients/{id}/addresses/{addressId}`,
`GET/POST /clients/{id}/contacts`, `GET/PATCH/DELETE /clients/{id}/contacts/{contactId}` — tudo num
único router, mesmo padrão de `007-clients.md` (Endereço/Contato documentados como sub-recursos do
mesmo dono).

`interfaces/schemas/client_schemas.py` — `ClientResponse`, `CreateClientRequest`,
`UpdateClientRequest`, `ClientContactResponse`, `CreateClientContactRequest`,
`UpdateClientContactRequest`; `interfaces/schemas/address_schemas.py` (compartilhado entre
`crm`/`maintenance`, mas cada módulo tem sua própria cópia dos schemas Pydantic de request/response
— schemas HTTP não são código de domínio compartilhável entre bounded contexts, só o
`AddressRepository`/entidade é).

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `CRM_CLIENT_NOT_FOUND` | 404 | Cliente não existe (ou pertence a outro tenant) |
| `CRM_CLIENT_DOCUMENT_ALREADY_EXISTS` | 409 | `uq_clientes_tenant_id_cnpj_cpf` |
| `ADDRESS_PRINCIPAL_ALREADY_EXISTS` | 409 | Segundo endereço `PRINCIPAL` para o mesmo dono |

`CRM_CLIENT_HAS_ACTIVE_TRIPS` (422, `DELETE /clients/{id}`) **não implementado neste lote** —
depende de `viagens`/`freight`, que ainda não existe no backend (Lote 4+). `DELETE` faz soft delete
incondicional por enquanto; o código de erro já está reservado no contrato (`007-clients.md`) e será
ligado quando `freight` existir, nunca inventado aqui como uma checagem contra uma tabela que ainda
não existe.

## Testes (D352)

- Unit: `Client.create()`/`.deactivate()`, invariantes de `ClientContact`.
- Integration: `SqlAlchemyClientRepository`/`SqlAlchemyClientContactRepository` contra Postgres
  real — tenant isolation, soft delete, unicidade de `document`.
- E2E: `POST /clients` → `GET` → `PATCH` → `POST /contacts` → `POST /addresses` → `DELETE` (soft
  delete, cliente não aparece mais em `GET /clients`) via HTTP real.
- Auditoria: `POST`/`DELETE /clients` geram `logs_auditoria` (`entidade_tipo=clientes`).
