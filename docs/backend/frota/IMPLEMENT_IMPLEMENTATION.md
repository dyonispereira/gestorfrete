# IMPLEMENT_IMPLEMENTATION.md — `Implemento`

Contrato: [`../../api/022-implements.md`](../../api/022-implements.md). DDL:
[`../../database/relational/004-frota.md`](../../database/relational/004-frota.md) (`implementos`).
RBAC: `fleet.implement.*` (`RBAC_MATRIX.md` §7.8).

Entidade independente, nunca um detalhe de Composição Veicular (D076, `022-implements.md`).

## Domain

```
modules/fleet/domain/
├── value_objects/body_type.py            # CARRETA/TANQUE/BAU/GRANELEIRO/PRANCHA/FRIGORIFICO/GAIOLA
├── value_objects/implement_availability.py  # DISPONIVEL / EM_USO / INATIVO
├── entities/implement.py                 # Implement(BaseAggregateRoot[UUID])
└── repositories/implement_repository.py
```

`Implement.create(codigo, placa, renavam, body_type, categoria_veiculo_id, capacidade_carga,
audit)` — nasce `DISPONIVEL`. `Implement.update(...)` inclui `availability_status` no mesmo
`PATCH` (`022-implements.md`: "o ciclo não tem complexidade que justifique um comando dedicado",
diferente de `Driver.block()`/`.unblock()`, Lote 3). Auditoria mais leve — `implementos` só tem
`criado_em`/`atualizado_em`/`excluido_em`, sem `_por` (mesmo padrão de `contatos_cliente`).

`DELETE` verifica `FLEET_IMPLEMENT_IN_COMPOSITION` (422) — **implementado de verdade** (diferente
de outros "fora de escopo" deste lote): a checagem só depende de
`composicoes_veiculares_implementos`, que existe nesta mesma migration. Consulta se o Implemento
aparece em alguma Composição vigente (`data_fim_vigencia IS NULL`) antes de desativar.

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `FLEET_IMPLEMENT_NOT_FOUND` | 404 | Implemento não existe (ou outro tenant) |
| `FLEET_IMPLEMENT_PLATE_ALREADY_EXISTS` | 409 | `uq_implementos_tenant_id_placa` |
| `FLEET_IMPLEMENT_IN_COMPOSITION` | 422 | `DELETE` com o Implemento em Composição vigente |

## Testes (D352)

- Unit: `Implement.create()`/`.update()`.
- Integration: Repository real — tenant isolation, soft delete, unicidade de placa.
- E2E: `POST /implementos` → `GET` → `PATCH` (`availability_status`) → `DELETE` via HTTP real;
  caso adicional — Implemento em Composição vigente → `DELETE` → `422`.
- Auditoria: `POST`/`DELETE /implementos` geram `logs_auditoria`.
