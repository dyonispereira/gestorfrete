# 043 — NF-e Referenciada

Bounded context proprietário: `documents` (D215). **Referência fiscal, não uma segunda NF-e criada
pelo GestorFrete** — o CT-e referencia a(s) NF-e do cliente/embarcador que acompanham a carga; a
transportadora nunca emite NF-e (`009-FISCAL.md`, fluxo principal item 4). Sem endpoint genérico de
NF-e — só este sub-recurso de CT-e (D225, D033: NF-e Referenciada só existe no contexto de um CT-e
específico).

## `GET /api/v1/ctes/{id}/nfe-referenciadas`

**Segurança**: `bearerAuth` + `documents.nfe_reference.view`.

**Responses**: `200` (`Pagination` de `ReferencedNFe`, `fiscal-schemas.md`), `401`, `403`, `404`,
`500`.

## `GET /api/v1/ctes/{id}/nfe-referenciadas/{nfeId}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/ctes/{id}/nfe-referenciadas`

`RBAC_MATRIX.md` §7.17 não tem `documents.nfe_reference.create` — reaproveitado `documents.
cte.issue` (adicionar referências de NF-e é parte de compor o CT-e antes/durante a emissão, mesmo
raciocínio de `.issue` cobrindo toda a montagem do documento em `039-cte.md`).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          access_key: { type: string }
        required: [access_key]
```

`access_key` deve ter 44 dígitos (`ck_nfe_referenciadas_chave_44_digitos`) — `400` caso contrário.

**Segurança**: `documents.cte.issue` (sem código dedicado — ver acima).

**Responses**: `201` (`ReferencedNFe`), `400`, `401`, `403`, `404` (CT-e não existe), `500`.

## Sem `PATCH`/`DELETE`

Uma referência de NF-e incorreta é removida e recriada como uma nova operação de composição do
CT-e enquanto ele ainda está `RASCUNHO`/`VALIDADO` — não modelado como edição própria neste lote
(RBAC não tem `.edit`/`.delete` para esta entidade; o CT-e como um todo ainda não foi
`AUTORIZADO` nesse estágio, então recriar via novo `POST` é suficiente).

## Como este documento cresce

Se o volume de NF-e referenciadas por CT-e crescer o bastante para justificar edição/remoção
individual, isso volta a `RBAC_MATRIX.md` primeiro (D283-style: código não existe, corrigir a
matriz antes do endpoint), nunca reaproveitando `.issue` para uma operação destrutiva.
