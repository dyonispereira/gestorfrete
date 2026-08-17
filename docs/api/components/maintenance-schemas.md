# components/maintenance-schemas.md — Schemas de Manutenção

Bounded context `maintenance` (D215). Schemas compartilhados por `026` a `031` — mesmo motivo de
`trip-schemas.md`/`fleet-schemas.md` existirem separados de `components/schemas.md`.

## `MaintenanceOrder` — Ordem de Serviço (Aggregate Root, D252)

Entidade única, **não** dividida em sub-schemas por fase — a organização em Abertura/Diagnóstico/
Orçamento/Aprovação/Execução/Encerramento é conceitual (`dictionary/004-manutencao.md`: "não é uma
mudança na máquina de estados — é a organização dos atributos por fase, dentro da mesma entidade"),
documentada em `026-maintenance-orders.md` via tabela, nunca como estrutura aninhada no schema —
inventar uma estrutura aninhada aqui transformaria a organização documental em algo que parece
schema/estado novo, exatamente o que o usuário pediu para evitar.

```yaml
MaintenanceOrder:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    codigo: { type: string, example: "OS-2026-000045" }
    vehicle_id: { $ref: "../components/schemas.md#/UUID", description: "`veiculo_tracionador_id` — FK, imutável." }
    vehicle_composition_id: { $ref: "../components/schemas.md#/UUID", description: "`composicao_veicular_id` — quando aplicável." }
    supplier_id: { $ref: "../components/schemas.md#/UUID", description: "`fornecedor_executor_id` — Fornecedor Executor, referencia `/suppliers` (Lote 3)." }
    type: { type: string, enum: [PREVENTIVA, CORRETIVA, EMERGENCIAL, GARANTIA], description: "`tipo` — atributo independente do status; todas as quatro seguem a mesma máquina de estados." }
    origin: { type: string, enum: [MANUAL, MANUTENCAO_PREVENTIVA_SUGERIDA, VIAGEM_INTERROMPIDA, CHECKLIST_REPROVADO, SUGESTAO_IA], readOnly: true, description: "`origem_abertura` — D256, nunca substitui `status`. Ver 031-maintenance-triggers.md." }
    problem_description: { type: string, description: "`descricao_problema` — o que foi relatado, distinto do diagnóstico técnico." }
    cause: { type: string, enum: [DESGASTE, QUEBRA, ACIDENTE, MAU_USO, INSPECAO, RECALL], description: "`causa` — só quando `type = CORRETIVA`." }
    root_cause: { type: string, description: "`causa_raiz` — distinta da causa imediata (D089)." }
    technical_diagnosis: { type: string, description: "`diagnostico_tecnico`." }
    mechanic_id: { $ref: "../components/schemas.md#/UUID", description: "`mecanico_id`." }
    predicted_cost: { type: string, readOnly: true, description: "`custo_previsto` — D254, soma dos Itens de OS, nunca digitável. Omitido/nulo para quem não tem `maintenance.work_order.view_cost`." }
    actual_cost: { type: string, readOnly: true, description: "`custo_realizado` — D254, congela em `FECHADA`. Mesma regra de visibilidade de `predicted_cost`." }
    requires_approval: { type: boolean, readOnly: true, description: "`necessita_aprovacao` — calculado comparando `predicted_cost` contra a alçada configurada em `settings` (D255), nunca setável diretamente." }
    completion_evidence_required: { type: boolean, readOnly: true, description: "`evidencia_conclusao_exigida` — D088, parâmetro de política do tenant, copiado na abertura." }
    status: { type: string, enum: [ABERTA, EM_DIAGNOSTICO, AGUARDANDO_APROVACAO, AGUARDANDO_PECA, EM_EXECUCAO, CONCLUIDA, FECHADA, CANCELADA], readOnly: true, description: "D253 — nunca alterado por PATCH. Ver tabela de comandos em 026-maintenance-orders.md." }
    execution_started_at: { type: string, format: date-time, readOnly: true, description: "`data_inicio_execucao`." }
    completed_at: { type: string, format: date-time, readOnly: true, description: "`data_conclusao`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, codigo, vehicle_id, type, origin, problem_description, status, audit]
```

## `MaintenanceOrderItem` — Item de OS

Sub-recurso, nunca criado fora de uma OS (D252) — `ordem_servico_id` vem sempre do path, nunca do
corpo. **D087 — nunca representa saldo/estoque**: `stock_part_id` é referência opcional ao registro
de Peça em Estoque (tabela física existe, sem endpoint próprio neste lote — ver "Fora de escopo" em
`027-maintenance-order-items.md`); o Item em si é sempre consumo, nunca saldo.

```yaml
MaintenanceOrderItem:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    cost_category: { type: string, enum: [PECAS, PNEUS, SERVICOS, TERCEIROS, MAO_DE_OBRA_INTERNA, MAO_DE_OBRA_TERCEIRIZADA, DESLOCAMENTO, OUTROS], description: "`categoria_custo`." }
    description: { type: string, description: "`descricao`." }
    stock_part_id: { $ref: "../components/schemas.md#/UUID", description: "`peca_estoque_id` — só quando `cost_category = PECAS` e a peça vem do Almoxarifado; referência sem endpoint de consulta próprio neste lote." }
    quantity: { type: string, description: "`quantidade` — maior que zero." }
    unit_value: { type: string, description: "`valor_unitario`." }
    total_value: { type: string, readOnly: true, description: "`valor_total` — `GENERATED ALWAYS AS (quantidade * valor_unitario)`, nunca digitável." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, cost_category, description, quantity, unit_value, total_value, audit]
```

## `MaintenanceApproval` — Aprovação de Custo

Sub-recurso de OS (D252). Campos de decisão espelham exatamente `aprovacoes_custo` — sem um campo
próprio de "alçada aplicada" (a tabela física não tem essa coluna; adicioná-la agora seria alterar o
Modelo Relacional a partir de um lote de API, fora do escopo — ver nota em
`028-maintenance-approvals.md`).

```yaml
MaintenanceApproval:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    level: { type: integer, description: "`nivel` — preparação para workflow multi-nível futuro, hoje sempre 1." }
    decision: { type: string, enum: [APROVADO, REJEITADO], readOnly: true, description: "`decisao` — nunca setável diretamente, só via commands/approve ou commands/reject." }
    justification: { type: string, description: "`justificativa` — obrigatória quando `decision = REJEITADO`." }
    actor_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`ator_id` — quem decidiu." }
    decided_at: { type: string, format: date-time, readOnly: true, description: "`data_hora`." }
  required: [id, level, decision, actor_id, decided_at]
```

## `MaintenancePreventivePlan` — Plano de Manutenção Preventiva

```yaml
MaintenancePreventivePlan:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    vehicle_id: { $ref: "../components/schemas.md#/UUID", description: "`veiculo_tracionador_id` — um dos dois (vehicle_id/vehicle_category_id) é obrigatório." }
    vehicle_category_id: { $ref: "../components/schemas.md#/UUID", description: "`categoria_veiculo_id`." }
    trigger_type: { type: string, enum: [QUILOMETRAGEM, HORAS_MOTOR, DIAS, CALENDARIO, MOTOR, TELEMETRIA, RECOMENDACAO_FABRICANTE], description: "`tipo_gatilho` — vocabulário extensível (D120-style); valores tirados literalmente do Enum físico, não do exemplo informal KM/HORAS/FABRICANTE." }
    interval_value: { type: string, description: "`valor_intervalo` — maior que zero; unidade depende de `trigger_type` (km/horas/dias)." }
    service_type_id: { $ref: "../components/schemas.md#/UUID", description: "`tipo_servico_id`." }
    status: { type: string, enum: [ATIVO, INATIVO], description: "`status`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, trigger_type, interval_value, service_type_id, status, audit]
```

## `ServiceType` — Tipo de Serviço

Reference Data pequena, pré-requisito obrigatório (`tipo_servico_id NOT NULL`) para criar um Plano —
já existe fisicamente (`tipos_servico`, `relational/005-manutencao.md`) e tem código RBAC próprio
(`maintenance.service_type.*`); exposta aqui como CRUD mínimo dentro de `029` para o Plano ser
realmente utilizável, não como entidade nova (ver nota em "Achados do Lote 6").

```yaml
ServiceType:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    name: { type: string, description: "`nome` — único por tenant." }
    status: { type: string, enum: [ATIVO, INATIVO], description: "`status`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, name, status, audit]
```

## `MaintenanceOrderStatusHistoryEntry` — Histórico Operacional

Leitura apenas (D257) — `ordens_servico_status_history`, nunca "Timeline Universal" (não existe
ainda para este agregado, ver `030-maintenance-history.md`).

```yaml
MaintenanceOrderStatusHistoryEntry:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    status: { type: string, enum: [ABERTA, EM_DIAGNOSTICO, AGUARDANDO_APROVACAO, AGUARDANDO_PECA, EM_EXECUCAO, CONCLUIDA, FECHADA, CANCELADA] }
    user_id: { $ref: "../components/schemas.md#/UUID", description: "`usuario_id` — nulo quando a transição é automática (derivada)." }
    origin: { type: string, description: "`origem` — quem/o que disparou a transição." }
    notes: { type: string, description: "`observacao` — obrigatória em `CANCELADA` e `AGUARDANDO_APROVACAO`." }
    occurred_at: { type: string, format: date-time, description: "`data_hora`." }
  required: [id, status, origin, occurred_at]
```

## Como este documento cresce

Peça em Estoque/Movimentação de Estoque/Solicitação de Peça **não** têm schema aqui — fora de
escopo deste lote (tabelas e RBAC existem, ver "Fora de escopo" em `026-maintenance-orders.md` e
`027-maintenance-order-items.md`).
