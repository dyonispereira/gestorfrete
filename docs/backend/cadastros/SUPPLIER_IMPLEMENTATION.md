# SUPPLIER_IMPLEMENTATION.md — `Fornecedor` (`modules/maintenance/`)

Contrato: [`../../api/008-suppliers.md`](../../api/008-suppliers.md),
[`../../api/011-addresses.md`](../../api/011-addresses.md) (sub-recurso). DDL:
[`../../database/relational/002-cadastros.md`](../../database/relational/002-cadastros.md)
(`fornecedores`). RBAC: `maintenance.supplier.*` (`RBAC_MATRIX.md` §7.2).

Mesmo padrão de `CLIENT_IMPLEMENTATION.md` — este documento só registra o que **difere**.

## Domain

```
modules/maintenance/domain/
├── value_objects/supplier_category.py  # SupplierCategory: PECA/RECAPAGEM/SEGURO/OFICINA/POSTO/
│                                          BORRACHARIA/GUINCHO/OUTRO (fornecedores_tipo_principal_enum)
├── value_objects/supplier_status.py    # ATIVO / INATIVO
├── entities/supplier.py                # Supplier(BaseAggregateRoot[UUID])
└── repositories/supplier_repository.py
```

`Supplier.create(codigo, razao_social, cnpj, telefone, category, audit)` — `category` é opcional
(`tipo_principal` nullable na DDL, "informativo, não restringe o que pode ser cadastrado" per
dictionary). Um único recurso `Supplier` cobre Oficina/Posto/Seguradora/Borracharia/Guincho/Peça —
D076, nunca uma subclasse ou tabela por categoria (`008-suppliers.md`).

## Infrastructure / Application / Interfaces

Mesma forma de `CLIENT_IMPLEMENTATION.md`: `SqlAlchemySupplierRepository` (tenant-filtered),
`CreateSupplierCommand`/`UpdateSupplierCommand`/`DeactivateSupplierCommand` +
`GetSupplierQuery`/`ListSupplierQuery`, auditoria em create/deactivate (D344). Sem sub-recurso de
Contato (`maintenance` não tem `.client_contact`-equivalente — `008-suppliers.md` confirma:
"`RBAC_MATRIX.md` só modela `crm.client_contact.*`", nunca inventado aqui, D227). Endereço delega
para `shared.addresses` com `owner_type=OwnerType.FORNECEDOR`.

`interfaces/api/supplier_router.py` — `GET/POST /suppliers`, `GET/PATCH/DELETE /suppliers/{id}`,
`GET/POST /suppliers/{id}/addresses`, `GET/PATCH/DELETE /suppliers/{id}/addresses/{addressId}`.

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `MAINTENANCE_SUPPLIER_NOT_FOUND` | 404 | Fornecedor não existe (ou outro tenant) |
| `MAINTENANCE_SUPPLIER_CNPJ_ALREADY_EXISTS` | 409 | `uq_fornecedores_tenant_id_cnpj` |

`MAINTENANCE_SUPPLIER_HAS_OPEN_ORDERS` (422, `DELETE`) **não implementado neste lote** — depende de
`ordens_servico` (`maintenance`, ainda não construído nesta fase de CRUD). `DELETE` faz soft delete
incondicional por enquanto, mesmo raciocínio de `CRM_CLIENT_HAS_ACTIVE_TRIPS`.

## Testes (D352)

Mesma cobertura de `CLIENT_IMPLEMENTATION.md`: unit (entidade), integration (Repository real,
tenant isolation, soft delete, unicidade de CNPJ), E2E (`POST`→`GET`→`PATCH`→`POST
/addresses`→`DELETE`), auditoria (`logs_auditoria` em create/deactivate).
