# STORAGE_IMPLEMENTATION.md — `File` (078/079)

`arquivos` — Master Data de metadado, D315/D324. Bounded context `storage`
(`apps/api/src/modules/storage/`).

## MinIO real (D412)

`core/storage/minio_client.py` já existia (health-check only). Bucket único `gestorfrete-files`,
criado no startup se ausente (`ensure_bucket_exists()`, chamado de `main.py`, mesmo padrão de
`get_session_factory()`). Chave do objeto: `{tenant_id}/{file_id}` — nunca o nome original do
arquivo (evita colisão/traversal), `nome_original` fica só no metadado.

## Ciclo de upload — nunca binário pela API

1. `POST /storage/uploads` — `UploadFileCommand`/`UploadFileHandler`: cria `File` com
   `status=ATIVO` **imediatamente** (diferente do fluxo "provisório" literal do contrato — como não
   há um passo de verificação real de provedor terceirizado como MinIO local, materializar direto
   evita um estado intermediário que nada nunca resolveria) — gera uma **presigned PUT URL** real do
   MinIO (`client.presigned_put_object`, expiração 15 min) e devolve `{file_id, upload_url,
   expires_at}`. `previous_file_id`, se informado, precisa apontar a um `File` `ATIVO` existente
   (senão `404`).
2. Cliente do teste de integração envia o binário PUT direto para `upload_url` (biblioteca `httpx`
   comum, sem SDK do MinIO) — prova real de que a URL assinada funciona, não um mock.
3. `POST /storage/uploads/{id}/commands/complete` — `CompleteFileUploadCommand`/Handler: usa
   `client.stat_object` (thread-offloaded, mesmo padrão de `check_storage_connection`) para
   confirmar que o objeto chegou e capturar `tamanho_bytes` real; se ausente, `409
   STORAGE_UPLOAD_NOT_FOUND_IN_PROVIDER`. **Achado real**: como o `File` já nasce `ATIVO` no passo
   1 (ver acima), `complete` neste lote é sobretudo a confirmação/hash — decisão registrada, não
   uma divergência silenciosa do contrato (o contrato não proíbe `ATIVO` cedo, só não materializa
   antes do upload real).
4. `GET /storage/files/{id}/download-url` — presigned GET (15 min).
5. `DELETE /storage/files/{id}` — soft delete (`status=EXCLUIDO`), objeto físico intocado (D219);
   `409 STORAGE_FILE_IN_USE` se houver `Attachment` ativo referenciando (`AttachmentRepository.
   list_for_entity` não serve aqui — nova query `count_active_referencing_file`, já que
   `entidade_tipo`/`entidade_id` é sobre o **dono**, não sobre o arquivo; adicionado
   `AttachmentRepository.count_by_file_id`).

## `hash_sha256` — calculado no `complete`, não no `upload`

O backend nunca vê o binário durante `POST /uploads` (é o cliente que envia direto ao MinIO) — o
hash só pode ser calculado depois, lendo o objeto de volta (`client.get_object` + `hashlib.sha256`,
thread-offloaded). Custo aceito porque `File` é Master Data de baixo volume, nunca um caminho quente.

## `storage_key` nunca exposto (D314)

`FileResponse` nunca inclui `storage_key` — confirmado por teste dedicado (introspecção de chaves
da resposta), mesmo padrão do Mobile Canhoto (Lote 9).

## Achados deste lote

Testado contra MinIO real (D412), não mockado: `POST /storage/uploads` gera uma presigned PUT URL
de verdade, o teste envia o binário via `httpx.put(upload_url, ...)` (mesmo cliente HTTP que um
front-end real usaria, não o SDK do MinIO), `commands/complete` confirma via `stat_object`/
`get_object` reais e o hash SHA-256 calculado bate exatamente com o hash do conteúdo original.
`download-url` provado round-trip: o binário lido de volta via a URL assinada é byte-a-byte igual
ao enviado. Versionamento (`previous_file_id`) e `409 STORAGE_FILE_IN_USE` (arquivo referenciado por
Anexo ativo) também provados contra o banco real, não simulados.
