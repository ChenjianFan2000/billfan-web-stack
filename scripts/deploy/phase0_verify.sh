#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-/var/www}"
ENV_FILE="${ENV_FILE:-/etc/qh-paper-assistant/app.env}"
PRIMARY_DOMAIN="${PRIMARY_DOMAIN:-billfan.cn}"
ALT_DOMAIN="${ALT_DOMAIN:-www.billfan.cn}"

log() {
  printf "[phase0/verify] %s\n" "$*"
}

check_cmd() {
  command -v "$1" >/dev/null 2>&1
}

print_domain_resolution() {
  for domain in "$PRIMARY_DOMAIN" "$ALT_DOMAIN"; do
    echo "--- DNS for $domain ---"
    if check_cmd getent; then
      getent ahosts "$domain" | cut -d" " -f1 | sort -u || true
    fi
  done
}

check_env_file() {
  echo "--- env file ---"
  if [ -f "$ENV_FILE" ]; then
    echo "ok: $ENV_FILE"
    if rg -n "CHANGE_ME|REPLACE_WITH_REAL_KEY" "$ENV_FILE" >/dev/null 2>&1; then
      echo "warn: env file still has placeholder values"
    else
      echo "ok: env file placeholders seem replaced"
    fi
  else
    echo "missing: $ENV_FILE"
  fi
}

check_runtime_files() {
  echo "--- runtime paths ---"
  for p in \
    "$ROOT_DIR/data/db.sqlite" \
    "$ROOT_DIR/data/pdfs" \
    "$ROOT_DIR/data/texts" \
    "$ROOT_DIR/data/chat_files" \
    "$ROOT_DIR/dist" \
    "$ROOT_DIR/.venv"; do
    if [ -e "$p" ]; then
      echo "ok: $p"
    else
      echo "missing: $p"
    fi
  done
}

check_services() {
  echo "--- systemd ---"
  if check_cmd systemctl; then
    systemctl is-enabled nginx >/dev/null 2>&1 && echo "ok: nginx enabled" || echo "warn: nginx not enabled"
    systemctl is-active nginx >/dev/null 2>&1 && echo "ok: nginx active" || echo "warn: nginx not active"

    if systemctl list-unit-files | rg -n "qh-paper-assistant.service" >/dev/null 2>&1; then
      systemctl is-enabled qh-paper-assistant >/dev/null 2>&1 && echo "ok: qh-paper-assistant enabled" || echo "warn: qh-paper-assistant not enabled"
      systemctl is-active qh-paper-assistant >/dev/null 2>&1 && echo "ok: qh-paper-assistant active" || echo "warn: qh-paper-assistant not active"
    else
      echo "warn: qh-paper-assistant.service not installed"
    fi
  else
    echo "warn: systemctl not found"
  fi
}

check_tls() {
  echo "--- tls cert ---"
  local cert_dir="/etc/letsencrypt/live/$PRIMARY_DOMAIN"
  if [ -f "$cert_dir/fullchain.pem" ] && [ -f "$cert_dir/privkey.pem" ]; then
    echo "ok: certificate files exist at $cert_dir"
  else
    echo "warn: certificate files missing at $cert_dir"
  fi
}

main() {
  log "starting verification"

  if check_cmd curl; then
    echo "--- public ip ---"
    if public_ip=$(curl -fsSL https://api.ipify.org 2>/dev/null); then
      echo "$public_ip"
    else
      echo "warn: unable to query public IP from api.ipify.org"
    fi
  fi

  print_domain_resolution
  check_env_file
  check_runtime_files
  check_services
  check_tls

  echo "--- listening ports ---"
  if check_cmd ss; then
    ss -lntp | rg ":80 |:443 |:8000 " || true
  fi

  log "verification complete"
}

main "$@"
