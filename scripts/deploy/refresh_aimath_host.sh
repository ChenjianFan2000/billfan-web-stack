#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-/var/www}"
NGINX_CONF_SRC="${ROOT_DIR}/deploy/nginx/aimath.billfan.cn.conf.example"
NGINX_CONF_DST="/etc/nginx/conf.d/aimath.billfan.cn.conf"
APP_SERVICE="${APP_SERVICE:-qh-paper-assistant.service}"
RESTART_APP_SERVICE="${RESTART_APP_SERVICE:-1}"
CERT_DIR="${CERT_DIR:-/etc/letsencrypt/live/aimath.billfan.cn}"

log() {
  printf "[aimath/deploy] %s\n" "$*"
}

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "please run as root" >&2
    exit 1
  fi
}

require_paths() {
  if [ ! -f "$NGINX_CONF_SRC" ]; then
    echo "missing nginx template: $NGINX_CONF_SRC" >&2
    exit 1
  fi

  if [ ! -f "$CERT_DIR/fullchain.pem" ] || [ ! -f "$CERT_DIR/privkey.pem" ]; then
    echo "missing certificate files in $CERT_DIR" >&2
    exit 1
  fi
}

restart_app_service() {
  if [ "$RESTART_APP_SERVICE" != "1" ]; then
    log "skipping app service restart"
    return
  fi

  if ! systemctl list-unit-files | grep -q "^${APP_SERVICE}[[:space:]]"; then
    log "app service not installed, skip: $APP_SERVICE"
    return
  fi

  systemctl restart "$APP_SERVICE"
  systemctl is-active "$APP_SERVICE" >/dev/null 2>&1
  log "app service restarted: $APP_SERVICE"
}

main() {
  require_root
  require_paths

  cp "$NGINX_CONF_SRC" "$NGINX_CONF_DST"
  nginx -t
  systemctl reload nginx
  log "nginx host config refreshed"

  restart_app_service
  log "aimath host is ready"
}

main "$@"
