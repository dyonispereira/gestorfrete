# 059 — Driver Signatures (Assinaturas Digitais)

Bounded context proprietário: `mobile` (D215) — `assinaturas_digitais` vive fisicamente em
`relational/009-app_motorista.md` e é consumida exclusivamente pelo App nesta sprint. Hoje só
`documento_tipo = CANHOTO` (Enum extensível).

## Sem `POST` direto — criação sempre via comando de Entrega

**A API mobile não duplica a lógica de assinatura.** `POST /api/v1/mobile/signatures` genérico
**não é criado** — o único `documento_tipo` real hoje (`CANHOTO`) já tem seu próprio ponto de
criação em `058-driver-deliveries.md` (`commands/pod`), que cria a `DigitalSignature` como parte da
mesma transação atômica do Canhoto. Isso corresponde literalmente à instrução do kickoff: "caso
pertença a uma ação de entrega, preferir o comando da entrega".

Se `assinaturas_digitais_documento_tipo_enum` ganhar um novo valor (ex: `CHECKLIST`, já reservado
no comentário da DDL) com um ponto de criação próprio e independente de outra entidade, **então**
este documento ganharia um `POST` dedicado — não antes, não especulativamente.

## `GET /api/v1/mobile/signatures`

Consulta — útil para o app confirmar que uma assinatura já capturada localmente foi de fato
persistida no servidor após sincronização.

**Segurança**: `bearerAuth` + `freight.delivery.view` — `RBAC_MATRIX.md` §7.13 não tem
`freight.pod.view` (só `.create`/`.attach` existem para Canhoto); reaproveitado `freight.
delivery.view`, já que o Canhoto (e sua assinatura) é sempre consultado no contexto de uma Entrega,
mesmo raciocínio de sub-recurso já aplicado em `019-trip-timeline.md`.

**Query parameters**: `page`/`limit`, `document_type` (`CANHOTO`), `document_id`.

**Responses**: `200` (`Pagination` de `DigitalSignature`, `components/mobile-schemas.md`), `401`,
`403`, `500`.

## `GET /api/v1/mobile/signatures/{id}`

**Responses**: `200` (`DigitalSignature`), `401`, `403`, `404`, `500`.

## Sem `PATCH`/`DELETE`

Assinatura é, por natureza, um registro pontual e imutável (D109-style, mesmo princípio de todo
artefato de evidência do sistema) — corrigir uma assinatura errada é recapturar (novo Canhoto), não
editar a existente.

## Como este documento cresce

Quando Checklist for formalizado (`056-driver-checklists.md`) e `CHECKLIST` for ativado no Enum,
este documento é revisado para decidir se a assinatura de Checklist também nasce via comando de
outra entidade (mesmo padrão do Canhoto) ou se justifica um `POST` próprio — decisão adiada, não
antecipada.
