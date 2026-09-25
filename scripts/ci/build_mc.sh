#!/usr/bin/env bash
# CI-only — compila o `mc` (MinIO Client) a partir do source oficial, pinado por tag + commit.
#
# Por quê: a imagem local construída em build_minio.sh (job e2e) precisa do `mc` porque o
# healthcheck já declarado em infra/compose/docker-compose.yml para o serviço `minio` é
# `mc ready local` — a imagem oficial `minio/minio` sempre empacotou os dois binários juntos, então
# uma imagem só com o servidor nunca passa nesse healthcheck. Mesmo princípio de
# build_minio.sh: nunca uma imagem de terceiro, nunca uma branch flutuante, tag+commit verificados
# antes de compilar.
set -euo pipefail

MC_TAG="RELEASE.2025-08-13T08-35-41Z"
MC_COMMIT="7394ce0dd2a80935aded936b09fa12cbb3cb8096"

OUT_BIN="${1:?Uso: build_mc.sh <caminho-de-saida-do-binario>}"

log() { echo "[build_mc.sh] $*"; }

SRC_DIR="$(mktemp -d)"
trap 'rm -rf "${SRC_DIR}"' EXIT

log "clonando minio/mc @ ${MC_TAG}"
git clone --quiet --depth 1 --branch "${MC_TAG}" https://github.com/minio/mc.git "${SRC_DIR}"

cd "${SRC_DIR}"
ACTUAL_COMMIT="$(git rev-parse HEAD)"
if [ "${ACTUAL_COMMIT}" != "${MC_COMMIT}" ]; then
  log "ERRO: a tag ${MC_TAG} não aponta para o commit pinado — build abortado."
  log "  esperado: ${MC_COMMIT}"
  log "  obtido:   ${ACTUAL_COMMIT}"
  exit 1
fi
log "commit verificado: ${ACTUAL_COMMIT}"

CGO_ENABLED=0 go build -tags kqueue -trimpath -o "${OUT_BIN}" .

log "mc ${MC_TAG} (${MC_COMMIT}) compilado em ${OUT_BIN}"
