# 085 — Exports (Exportações)

## D326 — reconciliado com o Lote 11, nenhum recurso novo criado

Mesma reconciliação de `084-reports.md`: o kickoff deste lote descreveu exatamente o padrão
assíncrono `POST /exports → PROCESSANDO → CONCLUÍDO → arquivo_id` com polling via
`GET /exports/{id}` — esse recurso já existe, construído no Lote 11: `069-exports.md`, bounded
context `reporting`, tabela física `exportacoes_geradas` (`relational/011-bi.md`).

```
POST /api/v1/reporting/exports   (já existente, 069-exports.md)
       ↓
status: PROCESSANDO
       ↓
status: CONCLUIDA + file_id   (D319 — sempre assíncrono, D307/D308 já registrados no Lote 11)
       ↓
GET /api/v1/reporting/exports/{id}   (polling, já existente)
```

## D319 formalizado

O texto do kickoff ("Operações grandes devem ser assíncronas") já era, literalmente, D307
(registrado no Lote 11: "Exportação é assíncrona quando superar limite operacional"). D319 (deste
lote) reafirma a mesma regra para o contexto transversal, sem introduzir um segundo mecanismo —
uma única implementação de exportação assíncrona em todo o sistema.

## D308 continua valendo

`file_id` referenciando `File` (`079-files.md`, D315) — desde o Lote 11 já era "arquivo pertence ao
Storage" (D308); com `079` agora formalizando o recurso `File` com metadados próprios, a referência
de `Export.file_id` passa a resolver contra um recurso real e consultável, não apenas um UUID
opaco.

## Como este documento cresce

Ver `069-exports.md` — toda evolução de exportação (novos `output_format`, retenção, etc.) entra
lá, nunca aqui. Este arquivo existe só para registrar a reconciliação D326 explicitamente, evitando
que um futuro lote tente recriar `/exports` por desconhecer que ele já existe.
