# CORRECTION_AND_REFERENCE_IMPLEMENTATION.md — Carta de Correção e NF-e Referenciada

Duas entidades internas, ambas sub-recursos append-only de CT-e (`042-carta-correcao.md`,
`043-nfe-referenciada.md`).

## `CorrectionLetter` — Carta de Correção

`POST /ctes/{id}/cartas-correcao` só aceito com CT-e pai `AUTORIZADO` —
`FISCAL_CTE_NOT_AUTHORIZED` (409) caso contrário. `numero_sequencial` sempre calculado pela
aplicação (`MAX(numero_sequencial) + 1` para o CT-e, começando em 1) — nunca aceito no corpo.
Nunca altera o CT-e pai (D282) — status do CT-e permanece `AUTORIZADO`. Sem `PATCH`/`DELETE`
(D109) — corrigir uma CC-e errada é emitir uma nova, `xml_arquivo_id` aceito no corpo apenas como
referência (simulação de resposta da SEFAZ nesta fundação, mesmo tratamento do restante do lote).

## `ReferencedNFe` — NF-e Referenciada

`POST /ctes/{id}/nfe-referenciadas` — `access_key` validada contra `^[0-9]{44}$`
(`ck_nfe_referenciadas_chave_44_digitos`) — `400` (`FISCAL_NFE_REFERENCE_INVALID_ACCESS_KEY`) caso
contrário, reforçado no Domain além do CHECK físico. Sem restrição de status do CT-e pai
documentada em `043` (diferente de Carta de Correção) — aceito em qualquer status do CT-e. Sem
`PATCH`/`DELETE`.

## Erros de domínio

`FISCAL_CTE_NOT_AUTHORIZED` (409, Carta de Correção), `FISCAL_NFE_REFERENCE_INVALID_ACCESS_KEY`
(400), `FISCAL_CTE_NOT_FOUND` (404, ambas).

## Auditoria e tenant isolation

Criação grava `logs_auditoria`. `SqlAlchemyCorrectionLetterRepository`/
`SqlAlchemyReferencedNfeRepository` filtram por `get_current_tenant_id()`.
