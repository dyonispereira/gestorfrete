# VEHICLE_IMPLEMENTATION.md — `Veículo Tracionador`, `Ficha Técnica`, `Documento do Veículo`, `Categoria de Veículo`

Contrato: [`../../api/020-vehicles.md`](../../api/020-vehicles.md),
[`../../api/021-vehicle-documents.md`](../../api/021-vehicle-documents.md). DDL:
[`../../database/relational/004-frota.md`](../../database/relational/004-frota.md)
(`veiculos_tracionadores`, `fichas_tecnicas_veiculo`, `documentos_veiculo`, `categorias_veiculo`).
RBAC: `fleet.vehicle.*`, `fleet.vehicle_technical_sheet.*`, `fleet.vehicle_document.*`,
`fleet.vehicle_category.*` (`RBAC_MATRIX.md` §7.8).

## Categoria de Veículo (D363) — sem router

```
modules/fleet/domain/entities/vehicle_category.py    # VehicleCategory(BaseAggregateRoot[UUID])
modules/fleet/domain/repositories/vehicle_category_repository.py
modules/fleet/infrastructure/persistence/models/vehicle_category_model.py
modules/fleet/infrastructure/persistence/repositories/sqlalchemy_vehicle_category_repository.py
```

Sem `application/`/`interfaces/` para Categoria — nenhum contrato OpenAPI existe (D363). Usado
internamente por `CreateVehicleHandler`/`CreateImplementHandler` (valida `categoria_id` existe) e
seedado diretamente pelo Repository nos testes de integração.

## Veículo Tracionador

```
modules/fleet/domain/
├── value_objects/vehicle_status.py       # ATIVO / INATIVO
├── entities/vehicle.py                   # Vehicle(BaseAggregateRoot[UUID])
└── repositories/vehicle_repository.py
```

`Vehicle.create(codigo, placa, renavam, fabricante, modelo, ano_fabricacao, categoria_veiculo_id,
filial_id, audit)`. `Vehicle.update(...)`. `Vehicle.deactivate(deactivated_by, now)` (soft delete,
D343). `FLEET_VEHICLE_HAS_ACTIVE_TRIP` (422, `DELETE`) **não implementado** — depende de
`alocacoes_recurso_viagem` (`freight`, Lote 5+); soft delete incondicional por enquanto, mesmo
raciocínio de `CRM_CLIENT_HAS_ACTIVE_TRIPS` (Lote 3).

`filial_id` aceito e armazenado, sem FK física ainda (`Filial` não existe, mesmo padrão de D355).

## Ficha Técnica do Veículo

Não-Aggregate-Root, 1:1 com Vehicle, Repository próprio (RBAC dedicado,
`fleet.vehicle_technical_sheet.*`). `chassi` único **na plataforma inteira** (não só por tenant —
`uq_fichas_tecnicas_veiculo_chassi` sem `tenant_id` na constraint, DDL confirma). `PATCH
/veiculos/{id}/technical-sheet` grava em duas tabelas fisicamente (`fabricante`/`modelo`/
`ano_fabricacao`/`categoria_veiculo_id` vivem em `veiculos_tracionadores`; o resto em
`fichas_tecnicas_veiculo`) — o handler orquestra os dois Repositories na mesma UoW, apresentando
uma resposta coesa (`fleet-schemas.md`'s `VehicleTechnicalSheet`), nunca dois `PATCH` separados do
cliente.

`404` quando o Veículo existe mas ainda não tem Ficha Técnica cadastrada (`020-vehicles.md`) —
distinto de "Veículo não existe".

## Documento do Veículo

Não-Aggregate-Root, N:1 com Vehicle, sub-recurso (`GET/POST/PATCH`, **sem `DELETE`** —
`fleet.vehicle_document.*` só tem `.view`/`.create`/`.attach`, D216). `arquivo_id` aceito, sem FK
física (`arquivos`/`storage` não implementado, mesma situação de `documentos_motorista.arquivo_id`,
Lote 3). `status` (`VALIDO`/`VENCIDO`) é `@property` calculada a partir de `data_validade`, mesmo
padrão de `DriverDocument.status` (Lote 3) — nunca uma segunda fonte de verdade.

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `FLEET_VEHICLE_NOT_FOUND` | 404 | Veículo não existe (ou outro tenant) |
| `FLEET_VEHICLE_PLATE_ALREADY_EXISTS` / `FLEET_VEHICLE_RENAVAM_ALREADY_EXISTS` | 409 | `uq_..._placa` / `uq_..._renavam` |
| `FLEET_CHASSIS_ALREADY_EXISTS` | 409 | `uq_fichas_tecnicas_veiculo_chassi` |

## Testes (D352)

- Unit: `Vehicle.create()`/`.deactivate()`, `VehicleDocument.status` calculado.
- Integration: Repositories reais — tenant isolation, soft delete, unicidade de placa/renavam/
  chassi (chassi cross-tenant, não só por tenant).
- E2E: `POST /veiculos` → `GET` → `PATCH` → `PATCH /technical-sheet` → `POST /documentos` →
  `DELETE` (soft delete) via HTTP real.
- Auditoria: `POST`/`DELETE /veiculos` geram `logs_auditoria`.
