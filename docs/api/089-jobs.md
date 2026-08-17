# 089 — Jobs (Execução de Job)

Bounded context proprietário: `integration` (D215). `execucoes_job` — Histórica (D037), Time
Series/técnica, particionada mensalmente — mesma categoria física de `eventos_fiscais` (Lote 8) e
`inferencias_ia` (Lote 11).

## `GET /api/v1/jobs`

Log técnico de execuções de tarefas assíncronas (relatórios pesados, reprocessamento de fila,
sugestão automática de manutenção preventiva, etc.).

**Segurança**: `bearerAuth` + `integration.job.view`.

**Query parameters**: `page`/`limit` via `cursor` (D191/D287 — Time Series nunca usa offset),
`job_type`, `result` (`SUCESSO`/`FALHA`), `started_at__gte`/`__lte`.

**Responses**: `200` (coleção cursor-paginada de `JobExecution`, `components/transversal-
schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/jobs/{id}`

**Responses**: `200` (`JobExecution`), `401`, `403`, `404`, `500`.

## `POST /api/v1/jobs/commands/trigger`

## D322 — jobs são autorizados individualmente, nunca um "executar comando arbitrário"

Pedido explícito do usuário: **este endpoint não permite disparar qualquer job arbitrário.**
`job_type` é validado contra o vocabulário de tipos de job já conhecidos pelo Backend (extensível,
D120-style, mas fechado no sentido de que o cliente nunca envia um nome livre que vira execução de
código) — o mesmo princípio de `integration.config.type`/`arquivos.origem`: vocabulário aberto para
*catalogação*, nunca para *execução* de algo não previsto.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          job_type: { type: string, description: "Deve corresponder a um tipo de job já registrado no Backend — nunca um nome arbitrário do cliente." }
          parameters: { type: object, description: "Parâmetros específicos do tipo de job, quando aplicável (ex.: período de um relatório pesado)." }
        required: [job_type]
```

**Segurança**: `integration.job.trigger` (**Alta** criticidade, **Aprovação: Administrador
Empresa** — pedido explícito do usuário). **Idempotency-Key**: recomendado (evita disparo duplicado
por retry de rede).

**Responses**: `202` (`JobExecution`, sem `data_hora_fim`/`resultado` ainda — execução é
assíncrona), `400` — `JOB_TYPE_NOT_REGISTERED`, `401`, `403`, `500`.

## Execução em si nunca é este endpoint

`POST /jobs/commands/trigger` **solicita** — não executa diretamente (mesmo princípio de D159,
`070-scheduled-updates.md`, Lote 11: o endpoint nunca é o worker). A execução real acontece em
processo de background (infraestrutura, fora deste contrato); este endpoint só cria o registro
`execucoes_job` e enfileira o disparo.

## Sem `PATCH`/`DELETE`

`execucoes_job` é Histórica (D037) — nunca editada nem removida após criada, mesma disciplina de
`eventos_fiscais`/`inferencias_ia`.

## Como este documento cresce

Se o produto pedir retry manual de um job falhado, isso é um comando aditivo
(`commands/retry`, referenciando o `job_type`/`parameters` da execução original) — não inventado
aqui por não ter sido pedido explicitamente.
