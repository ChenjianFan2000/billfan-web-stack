#!/usr/bin/env bash
# Read-only deployment checks. Does not create users, cast votes, or mutate state.
set -euo pipefail
DOMAIN=vote.billfan.cn
ROOT=/opt/dankou-vote/current

log() { printf '[dankou-vote/verify] %s\n' "$*"; }
check_health() {
    curl --fail --silent --show-error "$@" | python3 -c 'import json,sys; value=json.load(sys.stdin); sys.exit(0 if value.get("ok") is True and value.get("service")=="dankou-vote" else 1)'
}
for cmd in curl nginx systemctl python3; do
    command -v "$cmd" >/dev/null || { log "Missing command: $cmd"; exit 1; }
done
[[ "$(id -u)" == 0 ]] || { log 'Run with sudo to inspect configuration and service status.'; exit 1; }

nginx -t
systemctl is-active --quiet dankou-vote
systemctl is-enabled --quiet dankou-vote
[[ -L "$ROOT" ]]
[[ -f "$ROOT/services/vote/static/index.html" ]]
[[ -f "$ROOT/services/vote/static/admin.html" ]]
[[ -f "$ROOT/services/vote/static/players.html" ]]
[[ -s /etc/letsencrypt/live/vote.billfan.cn/fullchain.pem ]]
[[ -s /etc/letsencrypt/live/vote.billfan.cn/privkey.pem ]]
[[ -s /etc/dankou-vote/vote.env ]]
[[ -s /etc/dankou-vote/admin-url.txt ]]

python3 - <<'PY'
import os, stat
from pathlib import Path
for name in ('/etc/dankou-vote/vote.env', '/etc/dankou-vote/admin-url.txt'):
    p = Path(name)
    mode = stat.S_IMODE(p.stat().st_mode)
    if mode & 0o077:
        raise SystemExit(f'Credentials are readable outside root: {p}')
    if p.stat().st_uid != 0:
        raise SystemExit(f'Credentials should be owned by root: {p}')
PY

log 'Checking backend health.'
check_health --max-time 5 http://127.0.0.1:8020/api/health
log 'Checking HTTPS on this machine (DNS-independent).'
check_health --max-time 10 --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/api/health"
for route in / /players /admin; do
    curl --fail --silent --show-error --max-time 10 --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN$route" >/dev/null
    log "OK $route"
done
log 'Checking public DNS route and TLS.'
check_health --max-time 15 "https://$DOMAIN/api/health"
log 'Checking HTTP redirects to HTTPS.'
headers="$(curl --silent --show-error --max-time 10 --resolve "$DOMAIN:80:127.0.0.1" --dump-header - --output /dev/null "http://$DOMAIN/")"
if ! printf '%s' "$headers" | python3 -c 'import sys; s=sys.stdin.read().lower(); sys.exit(0 if "location: https://vote.billfan.cn/" in s and (" 308 " in s or " 301 " in s) else 1)'; then
    log 'HTTP redirect check failed.'
    exit 1
fi
log 'HTTP, HTTPS, static routes, service, and credential file permissions passed.'
log 'Use two separate phones for event rehearsal; this check does not simulate a live lock or cast votes.'
