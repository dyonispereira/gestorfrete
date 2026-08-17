# COMPOSITION_IMPLEMENTATION.md — `Composição Veicular`

Contrato: [`../../api/023-vehicle-compositions.md`](../../api/023-vehicle-compositions.md). DDL:
[`../../database/relational/004-frota.md`](../../database/relational/004-frota.md)
(`composicoes_veiculares`, `composicoes_veiculares_implementos`). RBAC:
`fleet.vehicle_composition.*` (`RBAC_MATRIX.md` §7.8 — só `.view`/`.create`/`.validate`, **sem**
`.edit`/`.delete`).

A parte mais crítica do lote — vigência, histórico como a própria tabela (D037), nunca `PATCH`
(D248).

## Domain

```
modules/fleet/domain/
├── value_objects/combination_type.py     # SIMPLES / BITREM / RODOTREM
├── value_objects/composition_status.py   # VALIDA / INVALIDA
├── entities/vehicle_composition.py       # VehicleComposition(BaseAggregateRoot[UUID])
└── repositories/vehicle_composition_repository.py
```

`VehicleComposition.create(veiculo_tracionador_id, tipo_combinacao, eixos_total, implementos:
list[tuple[UUID, int]], now)` — nasce `VALIDA`... na verdade nasce sem validação regulatória
aplicada ainda (ver `validate()` abaixo); `data_inicio_vigencia=now`, `data_fim_vigencia=None`.
`VehicleComposition.end_validity(now)` — fecha a vigência (`data_fim_vigencia=now`); chamado
**internamente** pelo Command Handler antes de criar uma nova composição para o mesmo veículo,
nunca por um endpoint próprio (D248: não existe "encerrar composição" como operação isolada —
`023-vehicle-compositions.md` registra isso como lacuna documentada, não inventada).
`VehicleComposition.validate(is_valid, now)` — usado por `POST .../commands/validate`.

**"Criar composição"/"Encerrar vigência"/"Trocar composição" são um único fluxo HTTP** (D248): o
Command Handler de `POST /vehicle-compositions` sempre verifica se já existe uma composição vigente
para o `tractor_unit_id` — se existir, chama `end_validity()` nela e insere a nova, tudo na mesma
transação/UoW. "Trocar composição" é exatamente esse fluxo; "Encerrar vigência" é o método de
domínio que ele reusa, nunca exposto como endpoint isolado.

**Validação de eixos (D368, placeholder)**: `_AXLE_RANGE_BY_COMBINATION_TYPE` — uma faixa
min/max de eixos por `combination_type` (`SIMPLES: 2-3`, `BITREM: 6-9`, `RODOTREM: 7-11`),
documentada como ilustrativa, **não** a tabela CONTRAN real (fora do escopo definir o algoritmo
exato, `023-vehicle-compositions.md`). Usada tanto em `POST` (`422
FLEET_COMPOSITION_AXLES_MISMATCH` se fora da faixa) quanto em `commands/validate` (define
`VALIDA`/`INVALIDA`).

## Infrastructure

`VehicleCompositionModel` + tabela de junção `composicoes_veiculares_implementos` (Table object,
sem soft delete — junção pura, mesmo padrão de `usuarios_papeis`, Lote 2) gerenciada dentro de
`SqlAlchemyVehicleCompositionRepository.add()`: substituição completa da lista de implementos a
cada `add()` (nunca incremental), mesmo padrão de `usuarios_papeis`.

`uq_composicoes_veiculares_vigente` (índice único parcial `WHERE data_fim_vigencia IS NULL`) é a
garantia física de "uma vigente por veículo" — o Handler fecha a antiga **antes** de inserir a
nova na mesma transação, então a constraint nunca é violada no caminho feliz; existe como rede de
segurança contra bugs futuros/concorrência, não como o único mecanismo.

## Interfaces

`interfaces/api/vehicle_composition_router.py` — `GET/POST /vehicle-compositions`,
`GET /vehicle-compositions/{id}`, `POST /vehicle-compositions/{id}/commands/validate`. **Sem
`PATCH`/`DELETE`** (D248, confirmado por RBAC — nenhum código `.edit`/`.delete`).

`vigente` query param (default `true`) filtra `data_fim_vigencia IS NULL`/`IS NOT NULL` — histórico
é só esse filtro na listagem, nunca um endpoint dedicado (D037).

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `FLEET_COMPOSITION_NOT_FOUND` | 404 | Composição não existe (ou outro tenant) |
| `FLEET_COMPOSITION_AXLES_MISMATCH` | 422 | Eixos totais fora da faixa esperada para o tipo de combinação (D368) |

## Testes (D352 + auditoria explícita pedida pelo usuário)

- Unit: `VehicleComposition.create()`/`.end_validity()`/`.validate()`, faixa de eixos por tipo.
- Integration: Repository real — tenant isolation, junção com Implementos substituída
  corretamente.
- E2E: `POST /vehicle-compositions` (SIMPLES) → `POST` de novo para o mesmo veículo (BITREM) →
  confirma a primeira tem `ends_at` preenchido e a segunda é a única com `ends_at: null` →
  `POST .../commands/validate` → `GET ?vigente=false` lista a fechada.
- **Auditoria dedicada (pedida pelo usuário)**: teste que cria N composições sucessivas para o
  mesmo veículo e, a cada passo, consulta o banco diretamente (`SELECT COUNT(*) WHERE
  data_fim_vigencia IS NULL`) confirmando que nunca há mais de uma linha vigente — prova o
  invariante por comportamento observado, não só assume que o índice único basta.
- Auditoria: `POST /vehicle-compositions` e `commands/validate` geram `logs_auditoria`.
