#!/usr/bin/env bash
# Production Readiness Hardening, Parte 8 — copia o dump mais recente (gerado por
# scripts/backup.sh) para uma SEGUNDA localização, fora do servidor onde o Postgres roda. Backup
# que só existe no mesmo host que pode falhar não é backup real — é uma cópia local, nada mais.
#
# Interface deliberadamente S3-compatível genérica, via `aws s3 cp` + --endpoint-url opcional — não
# é uma dependência forte de AWS. Qualquer provedor com API S3-compatível funciona (Backblaze B2,
# DigitalOcean Spaces, Wasabi, um MinIO hospedado em outro lugar, ou AWS S3 de verdade). Escolher O
# provedor real é uma decisão de deploy, tomada preenchendo as variáveis de ambiente abaixo — nunca
# hardcoded aqui, nenhum default de credencial.
set -euo pipefail

: "${GESTORFRETE_OFFSITE_S3_BUCKET:?GESTORFRETE_OFFSITE_S3_BUCKET não definido — a segunda localização é obrigatória, nunca opcional.}"
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID não definido (credencial do provedor S3-compativel de destino).}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY não definido (credencial do provedor S3-compativel de destino).}"

DUMP_FILE="${1:?Uso: backup_offsite_copy.sh <caminho-do-dump.dump>}"
if [ ! -f "${DUMP_FILE}" ]; then
  echo "[backup_offsite_copy.sh] ERRO: dump não encontrado: ${DUMP_FILE}" >&2
  exit 1
fi

# Vazio = endpoint padrão da AWS S3 real; qualquer outra URL = provedor S3-compatível equivalente.
OFFSITE_ENDPOINT="${GESTORFRETE_OFFSITE_S3_ENDPOINT:-}"
OFFSITE_PREFIX="${GESTORFRETE_OFFSITE_S3_PREFIX:-gestorfrete-backups}"

log() { echo "[backup_offsite_copy.sh] $(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

ENDPOINT_ARGS=()
if [ -n "${OFFSITE_ENDPOINT}" ]; then
  ENDPOINT_ARGS=(--endpoint-url "${OFFSITE_ENDPOINT}")
fi

DEST="s3://${GESTORFRETE_OFFSITE_S3_BUCKET}/${OFFSITE_PREFIX}/$(basename "${DUMP_FILE}")"
log "copiando ${DUMP_FILE} -> ${DEST}"

if ! aws s3 cp "${DUMP_FILE}" "${DEST}" "${ENDPOINT_ARGS[@]}"; then
  log "ERRO: cópia para a segunda localização falhou — o backup local NÃO foi apagado."
  exit 1
fi

log "verificando a cópia remota antes de considerar a operação bem-sucedida"
if ! aws s3 ls "${DEST}" "${ENDPOINT_ARGS[@]}" > /dev/null 2>&1; then
  log "ERRO: cópia remota não confirmada (upload pode ter falhado silenciosamente) — o backup local NÃO foi apagado."
  exit 1
fi

log "cópia externa confirmada: ${DEST}"
log "backup local preservado em ${DUMP_FILE} — este script nunca apaga a cópia local, só confirma a remota"
exit 0
