#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-/var/www}"
NGINX_MODE="${NGINX_MODE:-http}"
ENABLE_APP_SERVICE="${ENABLE_APP_SERVICE:-0}"

"$ROOT_DIR/scripts/deploy/phase0_install_system_deps.sh"
"$ROOT_DIR/scripts/deploy/phase0_prepare_runtime.sh"
NGINX_MODE="$NGINX_MODE" ENABLE_APP_SERVICE="$ENABLE_APP_SERVICE" \
  "$ROOT_DIR/scripts/deploy/phase0_deploy_configs.sh"
"$ROOT_DIR/scripts/deploy/phase0_verify.sh"
