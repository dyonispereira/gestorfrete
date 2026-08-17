# CTE_IMPLEMENTATION.md — CT-e

Aggregate Root de `documents`. Fonte: `flows/009-FISCAL.md` (máquina de 8 estados),
`relational/007-fiscal.md` (DDL), `039-cte.md` (HTTP).

## Máquina de estados

`RASCUNHO` (nasce via D396, `ViagemDespachada`) `→ VALIDADO` (`commands/validate`) `→ ASSINADO`
(`commands/sign`) `→ TRANSMITIDO` (`commands/transmit`) `→ {AUTORIZADO, DENEGADO}` (Externa,
resposta SEFAZ — `FiscalInternalTransitions`, D397) `→ CANCELADO` (`commands/cancel`, só a partir de
`AUTORIZADO`, dentro do prazo legal — validação de aplicação, sem coluna de prazo física, então
sempre aceito nesta fundação). `RASCUNHO`/`VALIDADO → INUTILIZADO` (`commands/inutilize`) — número
reservado nunca transmitido.

## Sem `POST /ctes` (D396)

Criado automaticamente por `DispatchTripHandler` (`freight`) chamando `CreateCteHandler`
(`documents`) — `numero`/`serie` capturados de `configuracoes_fiscais_tenant` via `SELECT ... FOR
UPDATE` (D399) no momento da criação (`RASCUNHO`), não da autorização — mesmo princípio de snapshot
D038, mas capturado mais cedo (`039-cte.md` não especifica em qual estado exato o número é
reservado; `RASCUNHO` é a leitura mais literal de "reservado mas nunca transmitido" no diagrama de
`009-FISCAL.md`).

## `commands/transmit` e a resposta da SEFAZ

`transmit` só move `ASSINADO→TRANSMITIDO` — a resposta (`AUTORIZADO`/`DENEGADO`) é sempre uma
chamada separada e posterior a `FiscalInternalTransitions.receive_cte_sefaz_response(...)` (D397),
nunca parte da resposta HTTP de `transmit` (D238 aplicado ao que já é conhecido no momento da
resposta). `chave_acesso`/`xml_arquivo_id`/`protocolo_sefaz`/`data_hora_autorizacao` só são
preenchidos por essa chamada.

## `valor_servico` na criação

`dictionary/007-fiscal.md` descreve `VALOR_SERVICO` como "capturado no momento da transmissão", mas
`ctes.valor_servico` é `NOT NULL` sem `DEFAULT` — precisa de um valor já no `INSERT` de `RASCUNHO`
(D396), antes de qualquer `commands/transmit`. Nenhum comando deste lote aceita `valor_servico` no
corpo (nem `039-cte.md` documenta um `PATCH /ctes/{id}`). Resolvido capturando de
`Trip.receita_prevista_snapshot` no momento da criação (`0.00` quando a Viagem ainda não tem esse
snapshot preenchido — cenário comum nesta fundação, já que Cotação/Programação da Viagem está fora
de escopo, D262) — mesma família de "aspiração em prosa não sustentada pela DDL congelada" já vista
em outros lotes (ex: Lote 6, "insere um novo valor acumulado" sobre `custo_realizado`).

## Idempotência (Auditoria #1 do usuário)

`receive_cte_sefaz_response` consulta `protocolo_sefaz` contra `uq_ctes_protocolo_sefaz` antes de
aplicar a transição — se o protocolo já foi registrado, a chamada é um no-op (retorna o CT-e como
está, não levanta erro, não grava um segundo `EventoFiscal` nem uma segunda linha de
`ctes_status_history`). Mesmo tratamento para `uq_eventos_fiscais_documento_protocolo`.

## `commands/cancel`/`commands/inutilize`

`notes` obrigatória em `cancel` (D010); gravada como `observacao` na linha de histórico.
`inutilize` não exige `notes` (não documentado como obrigatório em `039-cte.md`, diferente de
`cancel`).

## Erros de domínio

`FISCAL_CTE_NOT_FOUND` (404), `FISCAL_CTE_INVALID_TRANSITION` (409), `FISCAL_CERTIFICATE_EXPIRED`
(409, `commands/sign` quando `certificado_validade < hoje`).

**`FISCAL_CTE_VALIDATION_FAILED`** (`039-cte.md` documenta como resposta possível de
`commands/validate`, "dados incompletos/inconsistentes") **nunca é disparado nesta fundação** —
`CreateCteHandler` (D396) já preenche todos os campos `NOT NULL` de `ctes` no momento da criação
(`numero`/`serie` de `FiscalConfiguration`, `valor_servico` de `Trip.receita_prevista_snapshot` ou
`0.00`), então não existe um estado `RASCUNHO` genuinamente "incompleto" para `validate` rejeitar.
Uma primeira tentativa deste Handler invented a checagem `valor_servico > 0` — **removida**: como
`receita_prevista_snapshot` normalmente é `None`/`0.00` nesta fundação (Cotação/Programação da
Viagem fora de escopo, D262), essa checagem bloquearia o fluxo inteiro no caso mais comum, não só
um caso de borda. Mesma família "endpoint documentado, condição de bloqueio sempre vazia" de D394.

## Auditoria e tenant isolation

Toda transição grava `logs_auditoria` (D007) e uma linha em `ctes_status_history` — Auditoria #3 do
usuário: nenhuma transição (incluindo a resposta assíncrona) pula essa gravação.
`SqlAlchemyCteRepository` filtra por `get_current_tenant_id()`.
