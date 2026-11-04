#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-/var/www}"
NGINX_MODE="${NGINX_MODE:-http}"  # http | https
ENABLE_APP_SERVICE="${ENABLE_APP_SERVICE:-0}"

log() {
  printf "[phase0/config] %s\n" "$*"
}

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "please run as root" >&2
    exit 1
  fi
}

deploy_nginx() {
  local source_file

  case "$NGINX_MODE" in
    http)
      source_file="$ROOT_DIR/deploy/nginx/billfan.cn.http.conf"
      ;;
    https)
      source_file="$ROOT_DIR/deploy/nginx/billfan.cn.https.conf"
      ;;
    *)
      echo "invalid NGINX_MODE: $NGINX_MODE" >&2
      exit 1
      ;;
  esac

  if [ ! -f "$source_file" ]; then
    echo "missing nginx template: $source_file" >&2
    exit 1
  fi

  cp "$source_file" /etc/nginx/conf.d/billfan.cn.conf

  # Debian default site cleanup if present
  if [ -L /etc/nginx/sites-enabled/default ] || [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default
  fi

  nginx -t
  systemctl reload nginx
  log "nginx deployed in $NGINX_MODE mode"
}

deploy_systemd() {
  local service_src="$ROOT_DIR/deploy/systemd/qh-paper-assistant.service"
  local service_dst="/etc/systemd/system/qh-paper-assistant.service"

  if [ ! -f "$service_src" ]; then
    echo "missing systemd template: $service_src" >&2
    exit 1
  fi

  cp "$service_src" "$service_dst"
  systemctl daemon-reload

  if [ "$ENABLE_APP_SERVICE" = "1" ]; then
    systemctl enable --now qh-paper-assistant.service
    log "app service enabled and started"
  else
    systemctl enable qh-paper-assistant.service
    log "app service enabled (not started)"
  fi
}

main() {
  require_root
  deploy_nginx
  deploy_systemd
}

main "$@"
