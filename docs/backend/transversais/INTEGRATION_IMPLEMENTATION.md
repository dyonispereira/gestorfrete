# INTEGRATION_IMPLEMENTATION.md — Configuração de Integração/Webhook/Execução de Job (087/088/089)

Bounded context `integration` (`apps/api/src/modules/integration/`).

## Configuração de Integração (087) — CRUD simples

`credential_file_id` deve referenciar um `File` `ATIVO` (`404` se não). `status=COM_ERRO` nunca é
setado por nenhum comando HTTP (D321 é explícito: "derivado, nunca uma transição que o cliente
dispara") — como não existe adapter de infraestrutura real nesta fundação (nenhuma integração
externa de fato chamada), não há caminho de código que produza `COM_ERRO` neste lote; o valor existe
no enum e na resposta, documentado como inalcançável por ora, mesma disciplina de
`FISCAL_CTE_VALIDATION_FAILED` (D401) — nunca inventar um gatilho fake só para exercitar o valor.

## Webhook (088) — CRUD + entrega simulada (D413)

`signing_secret` gerado em `POST` (`secrets.token_hex(32)`), devolvido só na resposta de criação —
persistido como hash (`hash_token`, mesmo helper do Lote 9/D407) em `segredo_hmac_arquivo_id`... na
verdade a coluna é `UUID` (referência a `File`, cofre de segredos) — resolvido armazenando o hash do
segredo como um `File` `GERADO_PELO_SISTEMA` (`origin`) via o próprio `storage`, conteúdo nunca lido
de volta por nenhum endpoint (mesmo padrão de credencial de Integração). `commands/test` faz uma
chamada HTTP real e síncrona ao `target_url` (usa `httpx.AsyncClient`, timeout curto) — é o único
lugar deste lote que sai para a rede de verdade, porque o próprio contrato o define como uma chamada
síncrona imediata, não um evento assíncrono.

**Entrega real de evento de domínio → Webhook fica fora deste lote (D413)**: `088` documenta a
entrega como responsabilidade de worker assíncrono fora do contrato HTTP — implementar isso de
verdade exigiria um consumidor RabbitMQ real (infraestrutura não confirmada neste ambiente e, mais
importante, fora do próprio contrato). `WebhookInternalTransitions` (mesmo espírito de
`TripInternalTransitions`) expõe `simulate_delivery_attempt(webhook_id, success: bool)` — só chamado
diretamente por teste, nunca por HTTP — para provar que 3 falhas consecutivas suspendem o Webhook
(`status → SUSPENSO`, `numero_falhas_consecutivas` como estado em memória do simulador, nunca uma
coluna nova em `webhooks`, que já não tem uma).

## Execução de Job (089) — trigger enfileira, execução fica fora do contrato (D413/D322)

`POST /jobs/commands/trigger` valida `job_type` contra `JOB_TYPE_REGISTRY` (dict Python, vocabulário
fechado no sentido do D322 — nunca um nome livre do cliente), cria `execucoes_job` com
`data_hora_fim=None`/`resultado=None` (`202`, execução assíncrona) — igual a `089`'s próprio texto:
"este endpoint só cria o registro e enfileira o disparo". Execução real fica simulada via
`JobInternalTransitions.complete_job(job_id, result)`, mesmo princípio de todo `*InternalTransitions`
já usado desde o Lote 5.

`JOB_TYPE_REGISTRY` nesta fundação: `{"REPROCESSAMENTO_FILA_SINCRONIZACAO": ..., "EXPORTACAO_
RELATORIO": ...}` — dois tipos ilustrativos o suficiente para provar o mecanismo, sem inventar
integração real com nenhum subsistema pesado (Export/Report ficam fora deste lote via D326).

## Auditorias deste lote (candidatas)

1. **Credencial nunca em texto claro** — `IntegrationConfigResponse`/`WebhookResponse` nunca
   incluem o conteúdo do `File` referenciado, só o `id`.
2. **`signing_secret` exibido uma única vez** — presente no `201` de criação, ausente em qualquer
   `GET` subsequente do mesmo Webhook.
3. **3 falhas consecutivas suspendem o Webhook** — via `WebhookInternalTransitions`, nunca alcançável
   por HTTP.
4. **`job_type` desconhecido nunca cria execução** — `400 JOB_TYPE_NOT_REGISTERED`, nenhuma linha
   em `execucoes_job`.
5. **`integration.job.trigger` exige Administrador Empresa** — RBAC de alta criticidade, testado
   com um papel sem esse código recebendo `403`.

## Achados deste lote

As 5 auditorias candidatas confirmadas: `IntegrationConfigResponse`/`WebhookResponse` nunca expõem
conteúdo de credencial, só `credential_file_id`/referência; `signing_secret` presente só na resposta
do `POST` de criação, `None` em qualquer `GET` subsequente do mesmo Webhook — provado no mesmo
teste, não em dois testes separados que poderiam divergir; `WebhookInternalTransitions.
simulate_delivery_attempt` provado suspendendo o Webhook exatamente na 3ª falha consecutiva (ainda
`ATIVO` após a 2ª, `SUSPENSO` só após a 3ª — checado nas duas pontas, não só no resultado final);
`job_type` desconhecido (`EXECUTAR_CODIGO_ARBITRARIO`) rejeitado com `400 JOB_TYPE_NOT_REGISTERED`
sem criar nenhuma linha em `execucoes_job`; `integration.job.trigger` sem o código de permissão
correto devolve `403`, provando a Alta criticidade do comando. `JobInternalTransitions.complete_job`
provado fechando o ciclo assíncrono simulado — `GET /jobs/{id}` reflete `resultado=SUCESSO` depois
da chamada direta, nunca alcançável por HTTP.
