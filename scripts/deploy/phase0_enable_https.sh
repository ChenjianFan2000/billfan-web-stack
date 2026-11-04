#!/usr/bin/env bash
set -euo pipefail

PRIMARY_DOMAIN="${PRIMARY_DOMAIN:-billfan.cn}"
ALT_DOMAIN="${ALT_DOMAIN:-www.billfan.cn}"
EMAIL="${EMAIL:-}"
ROOT_DIR="${ROOT_DIR:-/var/www}"

log() {
  printf "[phase0/https] %s\n" "$*"
}

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "please run as root" >&2
    exit 1
  fi
}

require_email() {
  if [ -z "$EMAIL" ]; then
    echo "set EMAIL before running, e.g. EMAIL=admin@billfan.cn" >&2
    exit 1
  fi
}

main() {
  require_root
  require_email

  mkdir -p /var/www/certbot

  log "requesting letsencrypt certificate"
  certbot certonly --webroot \
    -w /var/www/certbot \
    -d "$PRIMARY_DOMAIN" \
    -d "$ALT_DOMAIN" \
    --agree-tos \
    --no-eff-email \
    --email "$EMAIL"

  log "switching nginx to https template"
  NGINX_MODE=https "$ROOT_DIR/scripts/deploy/phase0_deploy_configs.sh"

  log "testing certbot auto-renew"
  certbot renew --dry-run --non-interactive --no-random-sleep-on-renew

  if systemctl list-unit-files | grep -q '^certbot-renew\.timer'; then
    log "enabling certbot-renew.timer"
    systemctl enable --now certbot-renew.timer
  elif systemctl list-unit-files | grep -q '^certbot\.timer'; then
    log "enabling certbot.timer"
    systemctl enable --now certbot.timer
  fi

  log "https enabled"
}

main "$@"
