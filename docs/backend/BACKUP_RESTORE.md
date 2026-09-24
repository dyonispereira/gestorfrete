# BACKUP_RESTORE.md — Backup e Restore do Postgres

V1 Operational Hardening — item de INFRA pedido explicitamente pelo usuário. Escopo mínimo: o
Postgres é o único armazenamento com estado de negócio que não pode ser reconstruído (`viagens`,
`contas_pagar`/`contas_receber`, `ctes`/`mdfes`, `logs_auditoria`, tudo). Redis (idempotência,
`IDEMPOTENCY.md`) e RabbitMQ são caches/filas efêmeras por natureza — perdê-los não perde dado de
negócio, não fazem parte deste documento. MinIO (uploads/documentos) tem sua própria estratégia de
replicação de bucket, fora de escopo aqui (fica registrado como gap, não resolvido nesta rodada).

Não existia nenhuma estratégia de backup documentada ou automatizada antes deste documento — P0
registrado no Go-Live Audit.

## `pg_dump` automatizado

Formato `custom` (`-Fc`) — comprime, permite restore seletivo (schema/tabela específica) e restore
paralelo, ao contrário de um dump `.sql` texto puro.

```bash
#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${GESTORFRETE_BACKUP_DIR:-/var/backups/gestorfrete}"
BACKUP_FILE="${BACKUP_DIR}/gestorfrete_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

pg_dump \
  --format=custom \
  --file="${BACKUP_FILE}" \
  "${DATABASE_URL_SYNC}"  # postgresql://user:pass@host:5432/gestorfrete — sem +asyncpg, pg_dump é sync

# Falha se o dump ficou vazio/corrompido — nunca reporta sucesso de um backup inútil.
pg_restore --list "${BACKUP_FILE}" > /dev/null

echo "Backup gravado: ${BACKUP_FILE}"
```

Agendamento: `cron`/systemd timer diário fora do horário de pico de tráfego (a definir por
ambiente de produção real — não existe ainda um ambiente de produção real para calibrar isso).
Local: `docker-compose.yml`/`infra/` não tem nenhum serviço de agendamento hoje — este script roda
fora dos containers, num host com `pg_dump` da mesma major version do Postgres do
`docker-compose.yml` (`postgis/postgis:16-3.4-alpine`, ou seja `pg_dump` 16.x) e acesso de rede ao
`postgres` (porta `5432`, já exposta no compose).

## Retenção

Ponto de partida documentado (mesmo espírito de `IDEMPOTENCY.md`'s 24h — valor inicial, ajustável
com necessidade real, não uma lei imutável):

| Idade do backup | Retenção |
|---|---|
| Últimos 7 dias | Todos os dumps diários |
| 8–35 dias | 1 dump semanal |
| 36+ dias | 1 dump mensal, por 12 meses |

```bash
# Poda simples por idade de arquivo — roda depois de cada backup bem-sucedido.
find "${BACKUP_DIR}" -name 'gestorfrete_*.dump' -mtime +35 -delete
```

## Localização/configuração por ambiente

| Variável | Local (`docker-compose.yml`) | Produção (futura) |
|---|---|---|
| `GESTORFRETE_BACKUP_DIR` | `./backups` (bind mount, fora do volume `postgres_data`) | Bucket S3-compatible separado do banco — nunca no mesmo host físico do Postgres (backup que mora no mesmo disco que falha não é backup) |
| `DATABASE_URL_SYNC` | `postgresql://gestorfrete:gestorfrete@localhost:5432/gestorfrete` | Lido de secret manager, nunca hardcoded — mesmo princípio já aplicado a `Settings.jwt_secret_key`/`database_url` (`core/config/settings.py`), que hoje só têm defaults fracos, sem guard de produção (gap relacionado, registrado no Go-Live Audit, não fechado por este documento) |

## Procedimento de restore

```bash
# 1. Criar um banco novo, nunca restaurar por cima do banco vivo diretamente.
createdb -U gestorfrete gestorfrete_restore_test

# 2. Restaurar o dump mais recente.
pg_restore --dbname=gestorfrete_restore_test --clean --if-exists --no-owner \
  "${BACKUP_DIR}/gestorfrete_<timestamp>.dump"

# 3. Validar antes de promover: contagem de linhas nas tabelas de maior volume, Alembic no HEAD
#    esperado, uma consulta de negócio real (ex.: uma Viagem específica ainda existe com o status
#    correto).
psql -U gestorfrete -d gestorfrete_restore_test -c "SELECT version_num FROM alembic_version;"
psql -U gestorfrete -d gestorfrete_restore_test -c "SELECT count(*) FROM viagens;"

# 4. Só depois de validado: apontar a aplicação para o banco restaurado (troca de
#    DATABASE_URL + restart), nunca um DROP DATABASE do banco vivo como parte do procedimento
#    normal — isso é uma decisão separada, humana, depois que o restore já provou estar íntegro.
```

## Teste real de restore

Backup nunca testado é backup que não existe de fato — a falha só aparece quando já é tarde demais.
Mínimo exigido: rodar o procedimento de restore acima contra um banco descartável
(`gestorfrete_restore_test`) pelo menos uma vez por ciclo de retenção (mensal), como parte da
rotina operacional, não como um evento único de validação desta rodada. Sem essa disciplina
recorrente, este documento é só uma promessa — a mesma armadilha que `IDEMPOTENCY.md` já tinha
antes do V1 Operational Hardening Parte 6 (documentado, nunca executado).

## Fora de escopo desta rodada (não esquecido)

- Backup do bucket MinIO (uploads/documentos) — precisa de replicação/versionamento de objeto,
  mecanismo diferente de `pg_dump`.
- Point-in-time recovery (WAL archiving/`pgbackrest`) — o `pg_dump` diário acima cobre o caso de
  recuperação de desastre completo, não "recuperar para as 14h32 de terça"; PITR fica para quando
  o volume real de transações em produção justificar o investimento operacional adicional.
- Automação real do agendamento (cron/systemd/job de CI) — o script acima é o contrato, não ainda
  amarrado a um executor automático nesta rodada.
