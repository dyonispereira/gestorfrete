# 028 — Maintenance Approvals (Aprovações de Custo)

Bounded context proprietário: `maintenance` (D215). Sub-recurso de Ordem de Serviço (D252),
modelado como recurso próprio (não um campo da OS) porque tem ciclo de vida e ator distintos
(D225) — cada registro é uma decisão pontual e imutável (`dictionary/004-manutencao.md`: "registro
pontual, imutável após criado").

## D255 — alçada é consultada, nunca alterada aqui

`ORDEM_SERVICO.NECESSITA_APROVACAO` é calculado comparando `predicted_cost` contra a **Alçada de
Aprovação de Manutenção**, um parâmetro de configuração do tenant de posse do bounded context
`settings`/`administracao` — `maintenance` só o lê. Esse parâmetro **ainda não tem endpoint próprio**
em nenhum lote da API (nem `administracao` foi convertido em API ainda) — dependência explícita
(D242-style), não inventada aqui. `MaintenanceApproval` também não guarda um snapshot do valor da
alçada aplicada (a tabela física `aprovacoes_custo` não tem essa coluna); adicioná-la exigiria
alterar `relational/005-manutencao.md`, fora do escopo de um lote de API (arquitetura congelada) —
registrado como lacuna a considerar quando `settings` for modelado.

## `GET /api/v1/ordens-servico/{id}/aprovacoes`

**Segurança**: `bearerAuth` + `maintenance.work_order.view_cost` — `RBAC_MATRIX.md` §7.9 não tem um
`maintenance.cost_approval.view` dedicado (só `.approve`/`.reject`); reaproveitado `.view_cost`
(visualizar decisão de aprovação é, por natureza, visualizar informação de custo), lacuna
documentada em `components/security.md`.

**Responses**: `200` (`Pagination` de `MaintenanceApproval`, `maintenance-schemas.md`), `401`,
`403`, `404`, `500`.

## `GET /api/v1/ordens-servico/{id}/aprovacoes/{aprovacaoId}`

**Segurança**: idem acima. **Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/ordens-servico/{id}/aprovacoes/{aprovacaoId}/commands/approve`

Só válido quando a OS está em `AGUARDANDO_APROVACAO`. Resultado: cria o registro de decisão
`APROVADO` e transiciona a OS — conforme `003-MANUTENCAO.md` ("Gestor aprova — segue para verificar
disponibilidade de peça"), o resultado final é `AGUARDANDO_PECA` ou `EM_EXECUCAO` (a mesma
verificação de disponibilidade usada em `commands/concluir-diagnostico`,
`026-maintenance-orders.md`) — a resposta reflete o estado final, nunca o `EM_DIAGNOSTICO`
intermediário citado no fluxograma (D238).

**Segurança**: `maintenance.cost_approval.approve`. Nota: `RBAC_MATRIX.md` também tem
`maintenance.work_order.approve_cost`, aparentemente sobreposto — este contrato usa
`cost_approval.approve` por mapear 1:1 ao recurso Aprovação sendo modelado aqui; a sobreposição em
si é uma imprecisão de granularidade da matriz, registrada, não resolvida silenciosamente escolhendo
um dos dois sem explicar.

**Idempotency-Key**: obrigatório (D211 — aprovação é uma das operações críticas listadas).

```yaml
requestBody:
  required: false
  content:
    application/json:
      schema:
        type: object
        properties:
          justification: { type: string }
```

**Responses**: `200` (`MaintenanceOrder` — D238, estado resultante da OS, não só a Aprovação), `401`,
`403`, `404`, `409` — `MAINTENANCE_ORDER_INVALID_TRANSITION` (OS não está em
`AGUARDANDO_APROVACAO`), `500`.

## `POST /api/v1/ordens-servico/{id}/aprovacoes/{aprovacaoId}/commands/reject`

Cria o registro `REJEITADO` — `justification` obrigatória (D010, decisão explícita nunca implícita).
A OS **não** tem uma transição de "reprovado" própria em `003-MANUTENCAO.md` — na prática, uma
reprovação leva o solicitante a cancelar a OS (`commands/cancelar`, `026`) ou revisar os Itens para
reduzir o custo abaixo da alçada (nova tentativa de `commands/concluir-diagnostico`); o registro de
`REJEITADO` fica no histórico de Aprovações, mas **não move `status` sozinho** — coerente com D253 (a
única coisa que move `status` é um comando de OS, e reprovação de custo não é, por si, uma transição
listada na máquina de estados oficial).

**Segurança**: `maintenance.cost_approval.reject`. **Idempotency-Key**: obrigatório.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          justification: { type: string }
        required: [justification]
```

**Responses**: `200` (`MaintenanceApproval`), `400`, `401`, `403`, `404`, `409` —
`MAINTENANCE_ORDER_INVALID_TRANSITION` (OS não está em `AGUARDANDO_APROVACAO`), `500`.

## Sem `DELETE`/`PATCH`

Decisão de aprovação é imutável após criada (`dictionary/004-manutencao.md`) — sem código RBAC para
editar/excluir, sem endpoint. Uma decisão errada não é corrigida, é seguida por uma nova OS ou um
novo ciclo de diagnóstico, mesmo princípio de toda entidade Histórica do sistema (D037).

## Como este documento cresce

`level` (`nivel`) já está preparado para workflow multi-nível (`dictionary`: "preparação para
workflow em níveis... nenhuma migração de schema necessária quando aprovação em cascata for
implementada") — quando isso existir, este documento ganha uma seção descrevendo como múltiplos
níveis interagem; nenhuma mudança de endpoint prevista, só de regra de negócio interna.
