# TIMELINE_IMPLEMENTATION.md — Timeline da Viagem (Read Model)

`GET /api/v1/viagens/{id}/timeline` — implementação HTTP de D187/D022. **Sempre uma consulta,
nunca uma tabela** (`019-trip-timeline.md`). Nenhum `CommandHandler`/rota de escrita existe para
ela em nenhum lugar do código — mesma disciplina de `disponibilidade_veiculo` (Lote 4, D247), mas
aqui o motivo é ainda mais forte: a Timeline nem tem uma tabela física própria para eventualmente
ganhar um escritor.

## Fontes unidas neste lote (D372)

```sql
SELECT 'STATUS_OPERACIONAL'|'STATUS_FISCAL'|'STATUS_FINANCEIRO'|'STATUS_COMPOSTO' AS source, ...
    FROM viagem_status_history WHERE viagem_id = :id  -- dimensao decide o valor de `source`
UNION ALL
SELECT 'OCORRENCIA' AS source, ...
    FROM ocorrencias WHERE viagem_id = :id
ORDER BY occurred_at DESC   -- cursor: mais recente primeiro
```

Checklist/Abastecimento/Ordem de Serviço/Documento Fiscal/Anexos/Comentários **ficam de fora**
(`019-trip-timeline.md` já documenta isso fonte por fonte — nenhum tem endpoint de API ainda).
`TripTimelineEntry.source` já reserva os valores do enum completo (`CHECKLIST`/`ABASTECIMENTO`/
`ORDEM_SERVICO`/`DOCUMENTO_FISCAL`/`COMENTARIO`/`ANEXO`) para quando cada fonte ganhar seu próprio
lote — a consulta cresce (mais `UNION ALL`), o formato de resposta nunca muda.

## Implementação

`ListTripTimelineHandler` — não é uma Query genérica sobre um Repository de uma única tabela; monta
a consulta unida diretamente (SQL Core, `sqlalchemy.union_all`), filtra por `tenant_id` nas duas
pernas do `UNION`, ordena por `data_hora DESC`, aplica cursor (mesmo formato opaco
Base64(`{data_hora, id}`) já estabelecido em `list_odometer_readings.py`, Lote 4 — reaproveitado,
não reinventado).

`summary` (texto legível) é montado na Application a partir do `status`/`tipo` de cada linha —
nunca armazenado, sempre derivado no momento da leitura.

## Teste que prova a união (pedido explícito do usuário)

Cria uma Viagem, avança por pelo menos duas transições de status (incluindo uma automática via
D376) e registra uma Ocorrência; consulta a Timeline; confirma que a resposta contém entradas com
`source=STATUS_OPERACIONAL` (uma por transição real) **e** `source=OCORRENCIA`, ordenadas por
`occurred_at` — prova por comportamento observado que a Timeline é a fusão de duas fontes reais,
não uma tabela própria populada por um Handler de escrita (que não existe).

## Auditoria e tenant isolation

Somente leitura — nenhuma escrita própria para auditar. Tenant isolation garantido pelo `WHERE
tenant_id = ...` em ambas as pernas do `UNION ALL`, testado com uma segunda Viagem de outro tenant.
