#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-/var/www}"
APP_ENV_TARGET="${APP_ENV_TARGET:-/etc/qh-paper-assistant/app.env}"

log() {
  printf "[phase0/runtime] %s\n" "$*"
}

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "please run as root" >&2
    exit 1
  fi
}

create_dirs() {
  mkdir -p "$ROOT_DIR"/{app,dist,logs,certbot}
  mkdir -p "$ROOT_DIR"/data/{pdfs,texts,chat_files,exports}
  mkdir -p "$(dirname "$APP_ENV_TARGET")"
}

prepare_env_file() {
  if [ ! -f "$APP_ENV_TARGET" ]; then
    cp "$ROOT_DIR/deploy/env/app.env.example" "$APP_ENV_TARGET"
    log "created env file: $APP_ENV_TARGET"
  else
    log "env file already exists: $APP_ENV_TARGET"
  fi

  chmod 600 "$APP_ENV_TARGET"
}

prepare_venv() {
  if [ ! -d "$ROOT_DIR/.venv" ]; then
    python3 -m venv "$ROOT_DIR/.venv"
  fi

  "$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip setuptools wheel

  "$ROOT_DIR/.venv/bin/pip" install \
    fastapi \
    uvicorn \
    python-jose \
    passlib \
    pymupdf \
    pypdf \
    pdfplumber \
    reportlab \
    dashscope \
    httpx
}

main() {
  require_root
  create_dirs
  prepare_env_file
  prepare_venv
  log "runtime prepared"
}

main "$@"
