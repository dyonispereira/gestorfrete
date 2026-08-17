# 026 — Maintenance Orders (Ordens de Serviço)

Bounded context proprietário: `maintenance` (D215). Aggregate Root do módulo (D252) — máquina de
estados canônica em [`../flows/003-MANUTENCAO.md`](../flows/003-MANUTENCAO.md), atributos em
[`../database/dictionary/004-manutencao.md`](../database/dictionary/004-manutencao.md), DDL em
[`../database/relational/005-manutencao.md`](../database/relational/005-manutencao.md), RBAC em
`RBAC_MATRIX.md` §7.9 — todos lidos por completo antes de escrever este documento (D200 aplicado à
API, mesma disciplina de todo lote anterior).

## `GET /api/v1/ordens-servico`

**Segurança**: `bearerAuth` + `maintenance.work_order.view`.

**Query parameters**: `page`/`limit`, `search` (`codigo`/`descricao_problema`), `vehicle_id`
(`veiculo_tracionador_id`), `status`, `type` (`tipo`), `origin` (`origem_abertura`), `mechanic_id`
(`mecanico_id`), `supplier_id` (`fornecedor_executor_id`) — todos correspondem a colunas físicas
reais (D226), confirmados contra `relational/005-manutencao.md`.

**Responses**: `200` (`Pagination` de `MaintenanceOrder`, `maintenance-schemas.md`), `401`, `403`,
`500`.

**Visibilidade de custo**: `predicted_cost`/`actual_cost` só aparecem preenchidos quando o chamador
também tem `maintenance.work_order.view_cost` (código RBAC distinto de `.view`, confirmado em
`RBAC_MATRIX.md` — primeira vez neste contrato que uma permissão controla *campos* de uma resposta,
não o endpoint inteiro); sem ela, ambos os campos retornam `null`, nunca omitidos silenciosamente do
schema (o cliente sabe que o campo existe, só não tem acesso ao valor).

## `GET /api/v1/ordens-servico/{id}`

**Segurança**: `maintenance.work_order.view` (+ `.view_cost` para os campos de custo, mesma regra
acima). **Responses**: `200` (`MaintenanceOrder`), `401`, `403`, `404`, `500`.

## `POST /api/v1/ordens-servico`

Cria uma OS com `status = ABERTA`, `origin = MANUAL` sempre (D256 — este endpoint nunca aceita
`origin` no corpo; os outros quatro valores do Enum são reservados para consumidores de evento
futuros, ver `031-maintenance-triggers.md`).

**Segurança**: `maintenance.work_order.create`. **Idempotency-Key**: obrigatório (D211 — criação é
uma das operações críticas listadas).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          vehicle_id: { $ref: "components/schemas.md#/UUID" }
          vehicle_composition_id: { $ref: "components/schemas.md#/UUID" }
          supplier_id: { $ref: "components/schemas.md#/UUID" }
          type: { type: string, enum: [PREVENTIVA, CORRETIVA, EMERGENCIAL, GARANTIA] }
          problem_description: { type: string }
          cause: { type: string, enum: [DESGASTE, QUEBRA, ACIDENTE, MAU_USO, INSPECAO, RECALL] }
        required: [vehicle_id, type, problem_description]
```

`cause` só é aceito quando `type = CORRETIVA` (`ck_ordens_servico_causa_so_corretiva`) — `400` caso
contrário. `requires_approval`/`completion_evidence_required` nunca vêm do corpo — calculados/
copiados pela aplicação na criação (política de tenant, `settings`, D255).

**Responses**: `201` (`MaintenanceOrder`), `400`, `401`, `403`, `404` (Veículo/Composição/Fornecedor
não existe), `500`.

## `PATCH /api/v1/ordens-servico/{id}`

D229 — parcial. **Nunca altera `status`** (D253) — campos aceitos: `supplier_id`,
`problem_description`, `cause`, `root_cause`, `technical_diagnosis`, `mechanic_id`. Tentar enviar
`status` é ignorado silenciosamente pelo schema (a propriedade é `readOnly`, o gerador de cliente
nem serializa) — nunca um `400`/`409` por si só, mas o valor nunca é aplicado.

**Segurança**: `maintenance.work_order.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`,
`500`.

## `DELETE /api/v1/ordens-servico/{id}`

**D219 — soft delete.** Só permitido em `status = ABERTA` (antes de qualquer diagnóstico) — depois
disso, a forma correta de encerrar sem reparo é `commands/cancelar`, que preserva o histórico (a OS
já teve atividade real, nunca devendo desaparecer). Mesmo padrão de `DELETE /viagens/{id}` (Lote 4).

**Segurança**: `maintenance.work_order.edit` — `RBAC_MATRIX.md` §7.9 **não tem**
`maintenance.work_order.delete`; reaproveitado `.edit` por precedente direto de D240/D250-Lote5,
lacuna documentada (ver `components/security.md`).

**Responses**: `204`, `401`, `403`, `404`, `409` — `MAINTENANCE_ORDER_DELETE_INVALID_STATUS` (status
≠ `ABERTA`), `500`.

## Máquina de estados — comandos

**D253 — nenhum comando altera `status` diretamente via corpo; cada transição é um verbo próprio.**
Tabela abaixo cobre **toda** transição de `003-MANUTENCAO.md`, sem inventar nome novo.

| De | Para | Comando | Tipo | RBAC |
|---|---|---|---|---|
| `ABERTA` | `EM_DIAGNOSTICO` | `commands/iniciar-diagnostico` | Comando | `.edit` (sem código dedicado) |
| `EM_DIAGNOSTICO` | `AGUARDANDO_APROVACAO` | — | **Derivada** | — |
| `AGUARDANDO_APROVACAO` | `AGUARDANDO_PECA` \| `EM_EXECUCAO` | `028`: `commands/approve` | Comando (recurso externo) | `maintenance.cost_approval.approve` |
| `AGUARDANDO_APROVACAO` | `CANCELADA` | `commands/cancelar` | Comando | `.cancel` |
| `EM_DIAGNOSTICO` | `AGUARDANDO_PECA` \| `EM_EXECUCAO` | `commands/concluir-diagnostico` | Comando | `.edit` (sem código dedicado) |
| `AGUARDANDO_PECA` | `EM_EXECUCAO` | `commands/retomar-execucao` | Comando | `.edit` (sem código dedicado) |
| `EM_EXECUCAO` | `AGUARDANDO_PECA` | `commands/aguardar-peca` | Comando | `.edit` (sem código dedicado) |
| `EM_EXECUCAO` | `CONCLUIDA` | `commands/concluir` | Comando | `.edit` (sem código dedicado) |
| `CONCLUIDA` | `FECHADA` | `commands/fechar` | Comando | `.close` |
| `ABERTA`/`EM_DIAGNOSTICO`/`AGUARDANDO_PECA` | `CANCELADA` | `commands/cancelar` | Comando | `.cancel` |

### `EM_DIAGNOSTICO → AGUARDANDO_APROVACAO` — Derivada, não um comando

O diagrama de `003-MANUTENCAO.md` desenha esta seta partindo diretamente do nó `EM_DIAGNOSTICO`
(fora do losango "peça disponível?" mais abaixo) — lida literalmente, é uma regra automática, não
uma ação de ator: toda vez que um Item de OS é criado/editado (`027`) e o `predicted_cost`
recalculado ultrapassa a alçada configurada (`settings`, D255), a OS transiciona automaticamente
para `AGUARDANDO_APROVACAO`, publicando `OrdemServicoAprovacaoPendente`. Nenhum endpoint dispara
isso diretamente — é efeito colateral documentado de `POST/PATCH /ordens-servico/{id}/itens`.

### `commands/concluir-diagnostico` — branch derivado (peça disponível?)

Mecânico sinaliza diagnóstico concluído; a OS só aceita este comando se `requires_approval = false`
(caso contrário já teria migrado para `AGUARDANDO_APROVACAO` pela regra acima — `409` se tentado
fora de ordem). O resultado (`AGUARDANDO_PECA` ou `EM_EXECUCAO`) é decidido pela aplicação
consultando a disponibilidade dos Itens com `stock_part_id` preenchido — **nunca um campo
`peca_disponivel` no corpo da requisição** (o cliente não afirma disponibilidade, o servidor
verifica).

```yaml
requestBody:
  required: false
  content:
    application/json:
      schema:
        type: object
        properties:
          technical_diagnosis: { type: string }
          root_cause: { type: string }
```

**Responses**: `200` (`MaintenanceOrder`, D238 — sempre o estado resultante), `401`, `403`, `404`,
`409` — `MAINTENANCE_ORDER_INVALID_TRANSITION`, `500`.

### `commands/aguardar-peca` / `commands/retomar-execucao`

Cobrem o ciclo `EM_EXECUCAO ↔ AGUARDANDO_PECA` ("durante o reparo, identifica-se necessidade de
outra peça" / "peça recebida"). Disponíveis a Mecânico/Almoxarife. A tabela física de Solicitação de
Peça (`solicitacoes_peca`) existe mas não tem endpoint dedicado neste lote (ver "Fora de escopo") —
estes dois comandos operam só sobre `status` da OS, independente de existir ou não uma consulta
formal de Solicitação de Peça.

**Responses**: `200`, `401`, `403`, `404`, `409` — `MAINTENANCE_ORDER_INVALID_TRANSITION`, `500`.

### `commands/concluir`

`EM_EXECUCAO → CONCLUIDA`. Quando `completion_evidence_required = true` (D088, só relevante para
`type = PREVENTIVA`), exige ao menos uma evidência — modelada aqui como referência a Storage (D258),
nunca um sub-recurso genérico de Anexo/Comentário (fora de escopo, ver abaixo).

```yaml
requestBody:
  required: false
  content:
    application/json:
      schema:
        type: object
        properties:
          evidence_file_ids:
            type: array
            items: { $ref: "components/schemas.md#/UUID" }
            description: "D258 — referências a Storage; obrigatório e não-vazio quando `completion_evidence_required = true`."
```

**Responses**: `200`, `401`, `403`, `404`, `409` — `MAINTENANCE_ORDER_INVALID_TRANSITION` /
`MAINTENANCE_ORDER_EVIDENCE_REQUIRED`, `500`.

### `commands/fechar`

`CONCLUIDA → FECHADA`. `actual_cost` congela neste momento (D254) e é lançado no Centro de Custo do
veículo (`financial`, evento `OrdemServicoFechada`, já em `EVENT_MAP.md`).

**Segurança**: `maintenance.work_order.close`. **Idempotency-Key**: obrigatório (D211 —
encerramento).

**Responses**: `200`, `401`, `403`, `404`, `409` — `MAINTENANCE_ORDER_INVALID_TRANSITION`, `500`.

### `commands/cancelar`

Válido só a partir de `ABERTA`/`EM_DIAGNOSTICO`/`AGUARDANDO_APROVACAO`/`AGUARDANDO_PECA` — **nunca**
a partir de `EM_EXECUCAO` ou posterior (regra normativa explícita de `003-MANUTENCAO.md`: reparo já
iniciado é concluído, nunca cancelado). `notes` obrigatório no corpo (mesma regra de
`ordens_servico_status_history.observacao` para `CANCELADA`).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          notes: { type: string }
        required: [notes]
```

**Segurança**: `maintenance.work_order.cancel`. **Idempotency-Key**: recomendado.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409` — `MAINTENANCE_ORDER_INVALID_TRANSITION`,
`500`.

## Transições inválidas (reforço, nunca contornáveis por nenhum comando)

- Não é possível ir de `ABERTA` direto para `EM_EXECUCAO` — não existe comando que pule
  `EM_DIAGNOSTICO`.
- Não é possível cancelar a partir de `EM_EXECUCAO`/`CONCLUIDA`/`FECHADA` — `commands/cancelar`
  responde `409` fora das quatro origens válidas.
- Não é possível fechar sem passar por `CONCLUIDA` — `commands/fechar` só aceita origem `CONCLUIDA`.
- Não é possível reabrir uma OS `FECHADA` — nenhum comando tem `FECHADA` como origem; um problema
  recorrente é sempre uma nova OS (referenciando a anterior é responsabilidade de `descricao_problema`
  em texto livre neste lote — não existe campo estruturado de "OS anterior relacionada" na DDL atual).

## Fora de escopo, não esquecido

- **Peça em Estoque / Movimentação de Estoque / Solicitação de Peça**: tabelas físicas e códigos
  RBAC (`maintenance.part_stock.*`, `.stock_movement.*`, `.part_request.*`) existem, sem endpoint
  neste lote — `stock_part_id` em `MaintenanceOrderItem` é uma referência sem consulta própria.
- **Comentários/Anexos genéricos** (`maintenance.work_order.comment`/`.attach`): capacidades
  transversais D022/D023/D024 citadas em `003-MANUTENCAO.md`, sem endpoint em nenhum lote da API até
  agora (mesmo padrão de todos os lotes anteriores) — evidência de conclusão é resolvida via
  `evidence_file_ids` (Storage direto), não via um sub-recurso de Anexo genérico.
- **Pneu/Recapagem/Posicionamento** (RBAC §7.10) e **Checklist** (RBAC §7.11): bounded context
  `maintenance` mas fora do escopo desta OS — pertencem a `004-PNEUS.md`/`007-CHECKLIST.md`, fluxos
  ainda não convertidos em API.

## Como este documento cresce

Quando Solicitação de Peça/Estoque ganhar seu próprio lote, `commands/aguardar-peca`/
`retomar-execucao` passam a poder ser disparados também automaticamente por aquele fluxo (evento
`PecaSolicitada`/recebimento) — sem quebrar o contrato atual, que já trata esses comandos como
disponíveis a um ator humano independente de como a peça foi providenciada.
