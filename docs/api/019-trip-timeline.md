# 019 — Trip Timeline

Bounded context proprietário: `freight` (D215). Implementação HTTP de D187/D022 — Timeline
Universal é **sempre uma consulta**, nunca uma tabela própria armazenada.

## Somente leitura — nunca `POST /timeline`

```
GET /api/v1/viagens/{id}/timeline
```

Não existe (e nunca vai existir, D187/D236) um jeito de escrever diretamente na Timeline — cada
entrada é derivada de uma tabela real que já tem seu próprio endpoint de escrita (status,
Ocorrência, etc.); a Timeline é a projeção de leitura fundida, calculada em tempo de consulta
(`UNION ALL`), nunca persistida à parte.

## `GET /api/v1/viagens/{id}/timeline`

**Segurança**: `bearerAuth` + `freight.trip.view`/`.view_own` (mesma permissão de ler a própria
Viagem — a Timeline não introduz uma permissão própria, é uma visão sobre dados já protegidos por
suas permissões de origem).

**Paginação**: **Cursor**, não Offset — `viagem_status_history` é a fonte de maior volume
(`INDEXES.md`/`PARTITIONING.md`: partição mensal, Categoria Física `History`) e o padrão de
consulta é sempre "os eventos mais recentes primeiro" ou "a partir daqui para trás", nunca "página
42" (`PAGINATION.md`, regra por Categoria Física — seção 14 do pedido confirma exatamente esse
critério).

```
GET /api/v1/viagens/{id}/timeline?cursor=...&limit=50
```

**Responses**

| Código | Corpo |
|---|---|
| `200` | Coleção cursor-paginada de `TripTimelineEntry` (`trip-schemas.md`) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` |
| `500` | `InternalServerError` |

```json
{
  "data": [
    { "occurred_at": "2026-07-30T08:00:00Z", "source": "STATUS_OPERACIONAL", "summary": "Viagem criada (RASCUNHO)", "reference_id": "..." },
    { "occurred_at": "2026-07-30T08:45:00Z", "source": "STATUS_OPERACIONAL", "summary": "Despachada — EM_DESLOCAMENTO", "reference_id": "..." },
    { "occurred_at": "2026-07-30T13:10:00Z", "source": "STATUS_OPERACIONAL", "summary": "Entrega 1 concluída — EM_TRANSITO", "reference_id": "..." },
    { "occurred_at": "2026-07-30T16:40:00Z", "source": "OCORRENCIA", "summary": "Avaria registrada", "reference_id": "..." }
  ],
  "meta": { "pagination": { "next_cursor": "...", "has_more": true } }
}
```

Exemplo de leitura direto de `002-VIAGEM.md` ("Capacidades Transversais"), confirmando que o
formato não inventa nada além do que a Timeline já promete conceitualmente.

## Fontes incluídas hoje vs. visão completa do D187/`002-VIAGEM.md`

`002-VIAGEM.md` descreve a Timeline como a fusão de: os três `ViagemStatusHistory` (Operacional/
Fiscal/Financeiro/Composto), eventos de Checklist, Abastecimento, Ocorrência, Ordem de Serviço
(quando gerada por pane) e Documento Fiscal, comentários e anexos. **Neste lote, a consulta
implementável de fato é mais estreita** — honesto sobre o que existe fisicamente e tem API hoje:

| Fonte prometida | Incluída nesta versão? | Por quê |
|---|---|---|
| `viagem_status_history` (Operacional/Fiscal/Financeiro/Composto) | **Sim** | Tabela física, sempre populada |
| `ocorrencias` | **Sim** | Endpoint já existe (`017-trip-occurrences.md`) |
| Checklist | Não | `007-CHECKLIST.md` não escrito, sem tabela física ainda |
| Abastecimento | Não | Sem tabela física neste Modelo Relacional ainda (fora do escopo modelado até aqui) |
| Ordem de Serviço (pane) | Não | Existe fisicamente (`005-manutencao.md`), mas sem vínculo direto documentado a partir de `INTERROMPIDA` neste lote — candidato a uma próxima revisão desta consulta |
| Documento Fiscal (CT-e/MDF-e) | Não | `documents` ainda não tem lote de API próprio |
| Comentários (`comentarios`) | Não | Tabela compartilhada existe (D186), mas sem endpoint de API neste lote (mesma nota de `015-trip-deliveries.md` sobre Anexos) |
| Anexos (`anexos`) | Não | Idem |

A consulta cresce (mais `UNION ALL`) conforme cada fonte ganhar seu próprio lote de API — nunca
implementada como `JOIN` direto em tabela que a API ainda não expõe de forma independente.

## Como este documento cresce

Cada nova fonte entra como uma linha a mais na tabela acima e um novo valor no enum `source` de
`TripTimelineEntry` (`trip-schemas.md`) — nunca uma reformulação do formato de resposta em si.
