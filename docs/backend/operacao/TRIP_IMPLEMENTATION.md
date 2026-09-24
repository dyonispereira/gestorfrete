# TRIP_IMPLEMENTATION.md — Viagem (Trip)

Aggregate Root de `freight`. Fonte de verdade: `flows/002-VIAGEM.md` (máquina de estados),
`relational/003-operacao.md` (DDL), `014-trips.md`/`016-trip-resources.md`/`018-trip-status.md`
(HTTP).

## Modelo

`Trip(BaseAggregateRoot[UUID])` — `codigo`, `cliente_id`, `motorista_id`/`veiculo_tracionador_id`
(nulos até a primeira alocação), `data_programada`/`janela_programada`, as três dimensões
(`status_operacional`/`status_fiscal`/`status_financeiro`, cada uma seu próprio `StrEnum`),
snapshots, campos financeiros, `km_rodado`, `AuditMetadata`. `encerrada` **não é um campo gravável
da entidade** — é lido do banco (coluna `GENERATED`) só para exibição no DTO; nenhum método de
domínio o define.

## Três dimensões (D369)

`TripOperationalStatus`, `TripFiscalStatus`, `TripFinancialStatus` — três `StrEnum` independentes,
nunca colapsados. Só `TripOperationalStatus` tem comandos HTTP neste contrato (`018-trip-status.md`
— Fiscal/Financeiro são sempre `readOnly`, avançados só por consequência de evento de
`documents`/`financial`, que não existem ainda).

## `encerrada` (D019/D020)

```sql
encerrada BOOLEAN GENERATED ALWAYS AS (
    status_operacional = 'FINALIZADA' AND status_fiscal = 'MDFE_ENCERRADO' AND status_financeiro = 'RECEBIDA'
) STORED
```

Nenhum `Model`/`Repository`/`Handler` grava essa coluna — `INSERT`/`UPDATE` nunca a incluem na
lista de colunas. `TripModel.encerrada`/`.margem_prevista` são mapeadas com `sqlalchemy.Computed(...)`
(D382 — achado real rodando a suíte pela primeira vez: sem isso, o ORM inclui toda coluna mapeada
na lista de colunas de `INSERT`/`UPDATE` por padrão, e o Postgres rejeita qualquer valor explícito
em coluna `GENERATED ALWAYS`, mesmo que o Repository nunca a atribua manualmente). A auditoria pedida pelo usuário prova isso por dois ângulos: (1) uma tentativa de
`UPDATE viagens SET encerrada = true` direto via SQL falha com o erro nativo do Postgres para
coluna `GENERATED` (`cannot insert/update a generated column`); (2) avançar as três dimensões via
os métodos internos abaixo até seus estados terminais faz `encerrada` virar `true` sem que nenhum
código da aplicação a tenha escrito.

### D375 — como as dimensões Fiscal/Financeiro avançam nos testes

`documents`/`financial` não existem ainda. Mesmo padrão do Projetor de Disponibilidade (D247, Lote
4): dois métodos internos, nunca uma rota HTTP —

- `Trip.record_fiscal_transition(status: TripFiscalStatus, now, origin) -> None`
- `Trip.record_financial_transition(status: TripFinancialStatus, now, origin) -> None`

Cada um só grava a nova dimensão + insere a linha em `viagem_status_history`
(`dimensao='FISCAL'`/`'FINANCEIRO'`). Testes chamam os dois diretamente para simular o futuro
consumidor de `MDFeEncerrado`/`RecebimentoConfirmado`.

## Snapshots (D038/D071/D073) — D378

| Snapshot | Capturado quando |
|---|---|
| `cliente_snapshot` | `Trip.create(...)` — `cliente_id` já obrigatório no `POST` |
| `nome_motorista_snapshot`/`placa_veiculo_snapshot` | `Trip.dispatch(...)` (`LIBERADA→EM_DESLOCAMENTO`) — o momento em que a viagem realmente começa a ser executada |
| `receita_prevista_snapshot`/`tabela_preco_aplicada_snapshot_id` | **Nunca neste lote** — não existe fluxo de Cotação/aprovação de preço (D370); permanecem `NULL`, mesmo tratamento de `Vehicle.tracking_reference` (D250) |

Uma reatribuição de Motorista/Veículo **antes** do despacho não tem nada a congelar ainda
(referências vivas); **depois** do despacho, o snapshot já está fixo e uma troca de cavalo em rota
não o reabre (D073 — nunca ressincronizado). A auditoria de snapshot pedida pelo usuário testa
exatamente isso: cria Viagem (congela `cliente_snapshot`), despacha (congela
`nome_motorista_snapshot`/`placa_veiculo_snapshot`), altera o Cliente/Motorista de origem via seus
próprios módulos, consulta a Viagem de novo, confirma que os três valores não mudaram.

## Alocação de Recurso da Viagem (D188)

`TripAllocation(BaseEntity[UUID])` — pacote atômico (`motorista_id` + `veiculo_tracionador_id` +
`implemento_id` opcional), nunca três recursos independentes (`016-trip-resources.md`). Invariante
físico: `uq_alocacoes_recurso_viagem_vigente` (índice único parcial `WHERE status = 'VIGENTE'`) —
exatamente uma `VIGENTE` por Viagem.

`viagens.motorista_id`/`veiculo_tracionador_id` são **colunas denormalizadas** na própria Viagem
(a DDL as declara assim) — todo handler que cria/substitui uma Alocação também escreve essas duas
colunas em `Trip` na mesma transação (`Trip.set_current_allocation(...)`).

- `CreateTripAllocationHandler` (`POST /viagens/{id}/resources`): rejeita se já existe uma
  `VIGENTE` (`FREIGHT_TRIP_ALREADY_HAS_ALLOCATION`, 409); valida `Driver.fitness_status != BLOQUEADO`
  (`FREIGHT_DRIVER_NOT_FIT`, 422) e que o Veículo não tem alocação `VIGENTE` **em outra** Viagem
  (`FREIGHT_VEHICLE_UNAVAILABLE`, 422) — leituras cross-module de `drivers`/`fleet` (D356, aceito).
  Ao final, dispara a cascata D376 (`RASCUNHO→PLANEJADA→AGUARDANDO_CHECKLIST`).
- `ReallocateTripResourcesHandler` (`commands/reallocate-resources`): a `VIGENTE` atual vira
  `SUBSTITUIDA` (imutável a partir daí), uma nova linha `VIGENTE` é inserida com `motivo_troca`
  (`reason`, obrigatório no comando, opcional na base física). Permitido de `PLANEJADA` até
  `EM_ENTREGA` (`FREIGHT_TRIP_NOT_ALLOCATABLE` fora dessa janela). Publica `ViagemReatribuida`.
- **Reconciliado (V1 Operational Hardening, Parte 1)**: `FinishTripHandler`, `CancelarTripHandler`
  e `CloseAdministrativeTripHandler` buscam a Alocação `VIGENTE` da Viagem e chamam
  `TripAllocation.end()` (→ `ENCERRADA`) na mesma transação da transição de status — antes de
  `uow.commit()`, mesmo Aggregate (D188), sem cruzar módulo. `exists_vigente_for_vehicle_excluding_
  trip` (usada por `CreateTripAllocationHandler`) permanece inalterada; ela só enxerga `VIGENTE`,
  então uma Alocação `ENCERRADA` simplesmente para de bloquear o Veículo. Gap do Go-Live Audit
  fechado: antes, nenhum dos três handlers tocava a Alocação, que ficava `VIGENTE` para sempre.

## Máquina de estados — Status Operacional

Cada transição é um método do agregado `Trip`, levantando `DomainError`/`ConflictError` quando o
estado atual não permite. D235 (`018-trip-status.md`): erro de máquina de estados é sempre `409`
(`ConflictError`); erro de regra de negócio que não é sobre o estado é `422` (`DomainError`).

| Método | Transição | Tipo | HTTP |
|---|---|---|---|
| `create(...)` | `—→RASCUNHO` | Comando | `POST /viagens` |
| `set_current_allocation(...)` seguido de `plan(now)` | `RASCUNHO→PLANEJADA` | Derivada (D376) | `POST /resources` (sem comando próprio) |
| `await_checklist(now)` | `PLANEJADA→AGUARDANDO_CHECKLIST` | Derivada (D376) | nenhum — método interno, **deliberadamente separado** de `plan()` para a Viagem descansar observável em `PLANEJADA` e `commands/accept` (D129) fazer sentido |
| `release_after_checklist(now)` | `AGUARDANDO_CHECKLIST→LIBERADA` | Externa (D376) | nenhum — método interno |
| `dispatch(now, origin)` | `LIBERADA→EM_DESLOCAMENTO` | Comando | `commands/dispatch` (`origin='portal_gestor'`), `commands/start` (`origin='app_motorista'`) |
| `mark_collected(now)` | `EM_DESLOCAMENTO→CARREGANDO` | Externa (D376) | nenhum — método interno |
| `mark_manifest_checked(now)` | `CARREGANDO→EM_TRANSITO` (+ cascata p/ `EM_ENTREGA` se há Entrega `PENDENTE`) | Externa (D376) | nenhum — método interno |
| `accept(now)` | `PLANEJADA→PLANEJADA` (aditivo, D129/D379) | Comando | `commands/accept` |
| `interromper(now, notes, origin)` | `{EM_DESLOCAMENTO,CARREGANDO,EM_TRANSITO,EM_ENTREGA}→INTERROMPIDA` | Comando | `commands/interromper` |
| `retomar(now)` | `INTERROMPIDA→(estado anterior via histórico, D377)` | Comando | `commands/retomar` |
| `cancelar(now, notes)` | `{RASCUNHO,PLANEJADA,AGUARDANDO_CHECKLIST,LIBERADA,INTERROMPIDA}→CANCELADA` | Comando | `commands/cancelar` |
| `finish(now)` | `EM_ENTREGA→FINALIZADA` | Comando | `commands/finish` |
| `close_administrative(now, justification, actor_role)` | `{qualquer estado ativo}→FINALIZADA` (forçado) | Comando | `commands/close-administrative` |

`on_delivery_terminal(now, has_pending_deliveries)` — chamado por `UpdateDeliveryHandler` quando uma
Entrega atinge estado terminal (D237, o Aggregate Root controla, nunca o Controller): se ainda há
Entregas `PENDENTE`, registra o ciclo `EM_ENTREGA→EM_TRANSITO→EM_ENTREGA` (dois registros de
histórico, o sub-ciclo multi-drop documentado em `002-VIAGEM.md` como comportamento esperado, não
uma transição inválida); nunca avança sozinho para `FINALIZADA` — isso é sempre `commands/finish`,
explícito (`018-trip-status.md`: "pré-condição verificada pelo comando, não automática").

## Erros de domínio (prefixo `FREIGHT_`, D011)

`FREIGHT_TRIP_NOT_FOUND` (404), `FREIGHT_TRIP_INVALID_TRANSITION` (409), `FREIGHT_TRIP_ALREADY_
ACCEPTED` (409), `FREIGHT_TRIP_DELIVERIES_PENDING` (422, precondição de `finish`),
`FREIGHT_TRIP_CANNOT_DELETE_STARTED` (422), `FREIGHT_TRIP_ALREADY_HAS_ALLOCATION` (409),
`FREIGHT_TRIP_NOT_ALLOCATABLE` (422), `FREIGHT_DRIVER_NOT_FIT` (422), `FREIGHT_VEHICLE_UNAVAILABLE`
(422), `FREIGHT_UNKNOWN_CLIENT_ID`/`FREIGHT_UNKNOWN_DRIVER_ID`/`FREIGHT_UNKNOWN_VEHICLE_ID`/
`FREIGHT_UNKNOWN_IMPLEMENT_ID` (422 — referência cross-module inexistente), `FREIGHT_TRIP_NOTES_
REQUIRED` (400 — `interromper`/`cancelar` sem `notes`).

## Auditoria e tenant isolation

Toda transição grava em `logs_auditoria` (D007) e em `viagem_status_history` (D017/D018) — os dois
nunca se confundem: `logs_auditoria` é o rastro técnico genérico (quem/quando/o quê em qualquer
entidade do sistema); `viagem_status_history` é o histórico de negócio específico da máquina de
estados da Viagem, fonte de dados da Timeline. `SqlAlchemyTripRepository` filtra por
`get_current_tenant_id()` em toda consulta, mesmo padrão de todo repositório desde o Lote 2.
