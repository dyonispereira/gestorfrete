# 079 — Files (Arquivos)

Bounded context proprietário: `storage` (D215). `arquivos` — Master Data (metadados), D324/D107:
o binário nunca está aqui, apenas a referência lógica ao objeto físico no Storage.

## D315 — recurso de metadados, distinto do mecanismo

`File` é **o que o usuário trabalha**: nome, tipo, tamanho, hash, versão, status, origem — nunca
`MinIO Object`. O mecanismo de envio/leitura do binário (upload/download URL) é `078-storage.md`;
este documento é puramente a consulta do metadado já materializado.

## `GET /api/v1/storage/files`

**Segurança**: `bearerAuth` + `storage.file.view`.

**Query parameters**: `page`/`limit`, `mime_type`, `origin` (`UPLOAD_DIRETO`/`GERADO_PELO_SISTEMA`/
`IMPORTADO`), `status` (`ATIVO`/`EXCLUIDO`, default só `ATIVO`).

**Responses**: `200` (`Pagination` de `File`, `components/transversal-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/storage/files/{id}`

**Responses**: `200` (`File`), `401`, `403`, `404`, `500`.

## Campos — o que este recurso expõe, o que não expõe

| Campo | Origem | Observação |
|---|---|---|
| `name`/`mime_type`/`size_bytes`/`hash` | `arquivos` | D024, capturados no upload (`078`) |
| `version`/`previous_file_id` | `arquivos` | D324 — nova versão é sempre um novo `File`, nunca edição |
| `status` | `arquivos` | `ATIVO`/`EXCLUIDO` (soft delete, D219) |
| `origin` | `arquivos` | `UPLOAD_DIRETO`/`GERADO_PELO_SISTEMA`/`IMPORTADO` |
| **`storage_key`** | — | **Nunca exposto** — detalhe de infraestrutura interna (bucket/chave física), D314. Leitura do binário é sempre via `078`'s `download-url`, nunca por este campo |

## `GET /api/v1/storage/files/{id}/versions`

Navega a cadeia de versões (`previous_file_id`) do mais recente ao original.

**Segurança**: `storage.file.view`.

**Responses**: `200` (array de `File`, mais recente primeiro), `401`, `403`, `404`, `500`.

## Sem `POST`/`PATCH`

Criação é sempre via `078-storage.md`'s fluxo de upload (`POST /storage/uploads` +
`.../commands/complete`) — nunca um `POST /storage/files` direto, porque o metadado só existe depois
de o binário chegar ao Storage. Metadados são imutáveis após criados — corrigir um nome errado, por
exemplo, é enviar uma nova versão (`previous_file_id`), nunca um `PATCH` (D324, mesma disciplina de
`Metric`/D155).

## `DELETE` documentado em `078-storage.md`

`DELETE /storage/files/{id}` pertence ao documento do mecanismo (`078`) por ser parte do mesmo ciclo
de vida upload→leitura→exclusão — não duplicado aqui.

## Como este documento cresce

Se metadados adicionais forem necessários (ex.: dimensões de imagem, duração de vídeo), isso é
decisão de Domain/DDL primeiro (`arquivos` hoje só tem os campos de D024) — nunca inferido do
`mime_type` sem uma coluna física correspondente.
