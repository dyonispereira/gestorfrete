# 078 — Storage

Bounded context proprietário: `storage` (D215). Descreve o **mecanismo** de upload/download —
D315 separa este mecanismo do recurso `File` (`079-files.md`), que expõe apenas os metadados.

## D314 — domínio-agnóstico de provedor físico

Nenhum endpoint, schema ou mensagem de erro deste documento menciona MinIO/S3/Azure Blob — mesmo
princípio já aplicado a `AnalyticsCube` (Lote 11) e a Provedor de Rastreamento (D291, Lote 9). O
provedor físico é um adapter de infraestrutura, trocável sem alterar este contrato.

## Ciclo: iniciar → enviar diretamente ao Storage → concluir

```
POST /storage/uploads (metadados declarados)
        ↓
201 — upload_url (URL assinada, curta duração) + file_id provisório
        ↓
Cliente envia o binário DIRETAMENTE para upload_url (nunca via esta API — D314)
        ↓
POST /storage/uploads/{file_id}/commands/complete
        ↓
Backend verifica o objeto, calcula hash, materializa o File (arquivos, D324) — status ATIVO
```

Pedido explícito respeitado: **não criar download binário obrigatório pela API** — leitura também é
por URL assinada (`GET /storage/files/{id}/download-url`), nunca um endpoint que faz streaming do
binário através do backend.

## `POST /api/v1/storage/uploads`

Inicia o upload — declara os metadados antes de enviar o binário.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string, description: "Nome original do arquivo." }
          mime_type: { type: string }
          size_bytes: { type: integer }
          origin: { type: string, enum: [UPLOAD_DIRETO, IMPORTADO], description: "GERADO_PELO_SISTEMA nunca é aceito aqui — reservado a processos internos que chamam o Storage diretamente, fora desta API pública." }
          previous_file_id: { $ref: "components/schemas.md#/UUID", description: "Preenchido só quando este upload é uma nova versão de um File existente (D324 — versao incrementa, nunca sobrescreve)." }
        required: [name, mime_type, size_bytes, origin]
```

**Segurança**: `bearerAuth` + `storage.file.upload`.

**Responses**: `201` (`{file_id, upload_url, expires_at}`), `400`, `401`, `403`, `404`
(`previous_file_id` informado mas não existe), `500`.

## `POST /api/v1/storage/uploads/{id}/commands/complete`

Confirma que o binário já chegou ao Storage — o backend verifica a existência/tamanho/hash do
objeto antes de materializar o `File` (`079`) com `status = ATIVO`.

**Segurança**: `storage.file.upload` (mesma responsabilidade — iniciar e concluir são duas etapas do
mesmo verbo de negócio).

**Responses**: `200` (`File`, `components/transversal-schemas.md`), `401`, `403`, `404`, `409` —
`STORAGE_UPLOAD_NOT_FOUND_IN_PROVIDER` (cliente chamou `complete` sem enviar o binário), `500`.

## `GET /api/v1/storage/files/{id}/download-url`

Obtém uma URL temporária assinada para leitura do binário — nunca o conteúdo em si.

**Segurança**: `storage.file.view` (mesma permissão do metadado — quem pode ver os metadados pode
gerar uma URL de leitura).

**Responses**: `200` (`{download_url, expires_at}`), `401`, `403`, `404`, `500`.

## `DELETE /api/v1/storage/files/{id}`

**D219 — soft delete**: `status = EXCLUIDO` em `arquivos`, o objeto físico permanece no Storage até
uma rotina de expurgo de infraestrutura (fora deste contrato) — nunca removido sincronamente pela
API, mesmo princípio de todo `DELETE` já estabelecido nesta sprint.

**Segurança**: `storage.file.delete`.

**Responses**: `204`, `401`, `403`, `404`, `409` — `STORAGE_FILE_IN_USE` (referenciado por um Anexo
ativo, `080-attachments.md`), `500`.

## Versão — nunca sobrescreve

Enviar uma nova versão é sempre um novo `POST /storage/uploads` com `previous_file_id` preenchido —
nunca um `PATCH` no `File` existente (D324, mesmo padrão de `Metric.formula`/D155, Lote 11). O
`File` anterior permanece `ATIVO` e consultável; `079-files.md` documenta como navegar o histórico
de versões pela cadeia `previous_file_id`.

## Como este documento cresce

Se o produto precisar de upload multipart direto pela API (sem URL assinada, ex.: para clientes que
não suportam CORS de upload direto), isso é um novo comando aditivo — não substitui o padrão de URL
assinada, que continua sendo o caminho principal (D314).
