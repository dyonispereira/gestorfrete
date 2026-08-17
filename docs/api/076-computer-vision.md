# 076 — Computer Vision (Visão Computacional)

Bounded context proprietário: `ai` (D215). `leituras_visao_computacional` — Transactional, D161/
D164: resultado é sempre proposta, nunca aplicado automaticamente.

## Ciclo: arquivo → inferência → revisão humana (se necessária) → confirmação

```
arquivo_id (Storage, D107)
        ↓
Inferência de IA (072) processa a imagem
        ↓
Leitura de Visão Computacional criada — resultado_extraido é sempre proposta
        ↓
revisao_humana_necessaria = true?  ──não──► status = PROCESSADA (usável como está)
        │ sim
        ▼
Usuário confirma ou rejeita ──► status = CONFIRMADA / REJEITADA
```

Casos suportados hoje (`tipo_leitura`, Enum físico): `CANHOTO`, `AVARIA`, `MARCA_DE_FOGO`,
`IMPLEMENTO` — pneus/implementos entram via `MARCA_DE_FOGO`/`IMPLEMENTO`, não tipos novos
inventados aqui. Casos futuros do AgriHub (GestorPec, etc.) entrariam pelo Domain primeiro
(D101/D102), nunca antecipados neste contrato.

## `GET /api/v1/ai/computer-vision/readings`

**Segurança**: `bearerAuth` + `ai.computer_vision.view`.

**Query parameters**: `page`/`limit`, `reading_type` (`tipo_leitura`), `status`,
`human_review_required`.

**Responses**: `200` (`Pagination` de `ComputerVisionReading`, `ai-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/ai/computer-vision/readings/{id}`

**Responses**: `200` (`ComputerVisionReading`), `401`, `403`, `404`, `500`.

## `POST /api/v1/ai/computer-vision/readings/{id}/commands/confirm`

Só aplicável quando `human_review_required = true` e `status = PROCESSADA`. Confirma o resultado
extraído como correto — `usuario_confirmacao_id` é sempre capturado da sessão autenticada, nunca
aceito no corpo (mesmo princípio de D295 aplicado aqui).

**Segurança**: `ai.computer_vision.confirm`.

**Responses**: `200` (`ComputerVisionReading`, `status = CONFIRMADA`), `401`, `403`, `404`, `409` —
`AI_CV_READING_INVALID_TRANSITION` (não exige revisão ou já revisada), `500`.

## `POST /api/v1/ai/computer-vision/readings/{id}/commands/reject`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          reason: { type: string }
        required: [reason]
```

**Segurança**: `ai.computer_vision.confirm` (mesma responsabilidade — decidir sobre a leitura,
aceitando ou rejeitando, RBAC não distingue os dois verbos).

**Responses**: `200` (`status = REJEITADA`), `400`, `401`, `403`, `404`, `409`, `500`.

## Constraint de confirmação humana (já na DDL, preservada aqui)

`ck_leituras_visao_computacional_confirmacao_humana`: toda leitura `CONFIRMADA`/`REJEITADA` que
exigia revisão humana precisa ter `usuario_confirmacao_id` preenchido — o backend rejeita
(`409`/`422`) qualquer tentativa de transição que viole essa regra, nunca confiado apenas à
aplicação sem o reforço físico já existente.

## Sem `POST` de criação direta

Toda `ComputerVisionReading` nasce do processamento de uma Inferência (`072`) contra um
`arquivo_origem_id` já em Storage — o upload do arquivo em si e o disparo da inferência não são
modelados como um único endpoint aqui (fora de escopo — contrato de ingestão/upload ainda não
definido, mesmo espírito de D286/Lote 9).

## Como este documento cresce

Se `revisao_humana_necessaria` precisar de granularidade por campo (ex: só uma parte do resultado
exige revisão), isso é decisão de Domain/DDL primeiro — hoje é um booleano único por leitura.
