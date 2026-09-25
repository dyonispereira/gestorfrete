#!/usr/bin/env bash
# Pilot Hardening Final, Parte 1 — procedimento de restore real, para um ambiente controlado.
# Nunca toca no banco vivo: cria um banco descartável "<dbname>_restore_test", restaura o dump ali,
# valida (Alembic no HEAD esperado + contagem de linhas de negócio) e imprime os resultados —
# promover para o banco vivo continua sendo uma decisão manual e separada (docs/backend/
# BACKUP_RESTORE.md), nunca automatizada por este script.
set -euo pipefail

: "${DATABASE_URL_SYNC:?DATABASE_URL_SYNC não definido — ex.: postgresql://user:pass@host:5432/gestorfrete. Restore abortado, sem fallback silencioso.}"

DUMP_FILE="${1:?Uso: restore.sh <caminho-do-dump.dump>}"
if [ ! -f "${DUMP_FILE}" ]; then
  echo "[restore.sh] ERRO: arquivo de dump não encontrado: ${DUMP_FILE}" >&2
  exit 1
fi

log() {
  echo "[restore.sh] $(date -u +%Y-%m-%dT%H:%M:%SZ) $*"
}

# createdb/dropdb, ao contrário de psql/pg_dump/pg_restore, não aceitam uma URI de conexão como
# argumento posicional (esse positional é literalmente o nome do banco a criar/derrubar) — a
# conexão em si segue PGHOST/PGPORT/PGUSER/PGPASSWORD. Decompõe DATABASE_URL_SYNC uma vez aqui para
# que todo comando abaixo se conecte de forma consistente.
without_scheme="${DATABASE_URL_SYNC#postgresql://}"
userpass="${without_scheme%%@*}"
hostportdb="${without_scheme#*@}"
export PGUSER="${userpass%%:*}"
export PGPASSWORD="${userpass#*:}"
hostport="${hostportdb%%/*}"
export PGHOST="${hostport%%:*}"
export PGPORT="${hostport#*:}"
SOURCE_DB_NAME="${hostportdb#*/}"
RESTORE_DB_NAME="${SOURCE_DB_NAME}_restore_test"

log "dump: ${DUMP_FILE}"
log "banco de restore descartável: ${RESTORE_DB_NAME} (nunca o banco vivo '${SOURCE_DB_NAME}')"

log "recriando '${RESTORE_DB_NAME}' do zero (idempotente — restore anterior não deixa lixo)"
dropdb --if-exists "${RESTORE_DB_NAME}"
createdb -T template0 "${RESTORE_DB_NAME}"

log "restaurando dump em '${RESTORE_DB_NAME}'"
if ! pg_restore --dbname="${RESTORE_DB_NAME}" --clean --if-exists --no-owner "${DUMP_FILE}"; then
  log "ERRO: pg_restore falhou — restore não pode ser considerado íntegro"
  exit 1
fi

log "validando: versão do Alembic"
ALEMBIC_VERSION="$(psql -d "${RESTORE_DB_NAME}" -tA -c "SELECT version_num FROM alembic_version;" 2>/dev/null || echo "N/A (tabela alembic_version ausente neste dump)")"
log "alembic_version = ${ALEMBIC_VERSION}"

log "validando: contagem de linhas em tabelas de negócio"
for TABLE in viagens contas_pagar contas_receber logs_auditoria; do
  COUNT="$(psql -d "${RESTORE_DB_NAME}" -tA -c "SELECT count(*) FROM ${TABLE};" 2>/dev/null || echo "N/A (tabela ausente neste dump)")"
  log "  ${TABLE}: ${COUNT} linha(s)"
done

log "restore validado com sucesso em '${RESTORE_DB_NAME}'. Promoção para o banco vivo (troca de"
log "DATABASE_URL + restart) continua sendo uma decisão manual — este script nunca a executa."
exit 0
