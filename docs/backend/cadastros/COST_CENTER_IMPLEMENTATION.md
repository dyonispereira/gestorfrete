# COST_CENTER_IMPLEMENTATION.md — `Centro de Custo` (`modules/financial/`)

Contrato: [`../../api/013-cost-centers.md`](../../api/013-cost-centers.md). DDL:
[`../../database/relational/002-cadastros.md`](../../database/relational/002-cadastros.md)
(`centros_custo`). RBAC: `financial.cost_center.*` (`RBAC_MATRIX.md` §7.18) — apesar de
`centros_custo` viver fisicamente no lote de Cadastros, a posse RBAC é `financial`, mesma nota já
registrada para Fornecedor/`maintenance`.

Primeiro código real do bounded context `financial` (só scaffold vazio até este lote).

## `filial_id` nasce sem FK física (D355)

A DDL congelada declara `filial_id UUID REFERENCES filiais(id)` — mas `Filial`
(`tenancy`, contrato `006-branches.md`) não existe fisicamente ainda, só `Tenant` (Lote 2). Mesma
natureza de D196. `CostCenterModel.filial_id` é criado como `UUID` nullable, **sem**
`ForeignKey("filiais.id")`; documentado aqui, não uma correção da DDL — a constraint é adicionada
numa migration futura, quando `Filial` for implementada (mesmo raciocínio de D250, não
retrofitar/inventar dependência de módulo ainda não publicado). O campo continua existindo e sendo
aceito no `POST`/`PATCH` (`branch_id` no contrato) — só a integridade referencial física fica
pendente, a aplicação nunca valida contra uma tabela inexistente.

## Centro de Custo é cadastro mestre puro (reforço de D090)

Nenhum campo de saldo/indicador/valor acumulado no schema — confirmado tanto na DDL
(`relational/002-cadastros.md`: "guarda só identidade e classificação") quanto no contrato
(`013-cost-centers.md`). Qualquer "custo por Centro de Custo" é responsabilidade futura de
`analytics`, nunca calculado ou armazenado aqui.

## Domain

```
modules/financial/domain/
├── value_objects/cost_center_status.py   # ATIVO / INATIVO
├── entities/cost_center.py               # CostCenter(BaseAggregateRoot[UUID])
└── repositories/cost_center_repository.py
```

`CostCenter.create(codigo, codigo_contabil, nome, filial_id, audit)` — `filial_id` é
`uuid.UUID | None`, aceito e armazenado, nunca validado contra uma tabela `Filial` que não existe
(ver nota acima). `CostCenter.update(...)` — sem `.deactivate()` dedicado: desativação é só
`update(status=INATIVO)` (`013-cost-centers.md`: "Desativação é via PATCH, coerente com um Centro
de Custo já referenciado por lançamentos financeiros históricos nunca poder desaparecer").

## Infrastructure

`CostCenterModel` — tabela `centros_custo`. `SqlAlchemyCostCenterRepository` — tenant-filtered
(D338/D339).

## Application

`CreateCostCenterCommand`/`UpdateCostCenterCommand` + `GetCostCenterQuery`/`ListCostCentersQuery`.
Auditoria (D344) em create/update. **Sem** `DeleteCostCenterCommand` — não existe endpoint
`DELETE` (ver abaixo).

## Interfaces

`interfaces/api/cost_center_router.py` (primeiro router de `financial`, registrado em
`interfaces/api/v1/router.py`) — `GET/POST /cost-centers`, `GET/PATCH /cost-centers/{id}`. **Sem**
`DELETE` — `RBAC_MATRIX.md` não tem `financial.cost_center.delete` (confirmado por grep, D216
proíbe inventar o código; sem a Permissão, não há endpoint, `013-cost-centers.md`).

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `FINANCIAL_COST_CENTER_NOT_FOUND` | 404 | Centro de Custo não existe (ou outro tenant) |
| `FINANCIAL_COST_CENTER_CODE_ALREADY_EXISTS` | 409 | `uq_centros_custo_tenant_id_codigo_contabil` |

## Testes (D352)

- Unit: `CostCenter.create()`/`.update()`.
- Integration: `SqlAlchemyCostCenterRepository` contra Postgres real — tenant isolation, unicidade
  de `codigo_contabil`, `filial_id` nullable aceito sem erro (confirma que a ausência da FK física
  não quebra a inserção).
- E2E: `POST /cost-centers` → `GET` → `PATCH` (`status: INATIVO`) via HTTP real. Confirma também
  que `DELETE /cost-centers/{id}` retorna `405 Method Not Allowed` (rota nunca registrada).
- Auditoria: `POST`/`PATCH /cost-centers` geram `logs_auditoria`.
