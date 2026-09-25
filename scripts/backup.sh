#!/usr/bin/env bash
# Pilot Hardening Final, Parte 1 — backup real do Postgres, materializando o contrato já
# documentado em docs/backend/BACKUP_RESTORE.md (mesmas variáveis, mesmo nome de arquivo, mesma
# política de retenção). Requer pg_dump/pg_restore da mesma major version do Postgres do
# docker-compose (postgis/postgis:16-3.4-alpine → pg_dump 16.x) no PATH.
set -euo pipefail

: "${DATABASE_URL_SYNC:?DATABASE_URL_SYNC não definido — ex.: postgresql://user:pass@host:5432/gestorfrete (sem +asyncpg, pg_dump é sync). Backup abortado, sem fallback silencioso.}"

BACKUP_DIR="${GESTORFRETE_BACKUP_DIR:-/var/backups/gestorfrete}"
RETENTION_DAYS="${GESTORFRETE_BACKUP_RETENTION_DAYS:-35}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="${BACKUP_DIR}/gestorfrete_${TIMESTAMP}.dump"

log() {
  echo "[backup.sh] $(date -u +%Y-%m-%dT%H:%M:%SZ) $*"
}

mkdir -p "${BACKUP_DIR}"

log "iniciando pg_dump --format=custom -> ${BACKUP_FILE}"
if ! pg_dump --format=custom --file="${BACKUP_FILE}" "${DATABASE_URL_SYNC}"; then
  log "ERRO: pg_dump falhou — nenhum backup válido foi produzido"
  rm -f "${BACKUP_FILE}"
  exit 1
fi

log "validando integridade do dump (pg_restore --list)"
if ! pg_restore --list "${BACKUP_FILE}" > /dev/null; then
  log "ERRO: dump gerado está corrompido/vazio — não reportando sucesso de um backup inútil"
  rm -f "${BACKUP_FILE}"
  exit 1
fi

BACKUP_SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"
log "backup gravado com sucesso: ${BACKUP_FILE} (${BACKUP_SIZE})"

log "aplicando retenção: removendo dumps com mais de ${RETENTION_DAYS} dias em ${BACKUP_DIR}"
PRUNED_COUNT="$(find "${BACKUP_DIR}" -name 'gestorfrete_*.dump' -mtime "+${RETENTION_DAYS}" -print -delete | wc -l | tr -d ' ')"
log "retenção aplicada: ${PRUNED_COUNT} dump(s) antigo(s) removido(s)"

log "concluído"
exit 0
