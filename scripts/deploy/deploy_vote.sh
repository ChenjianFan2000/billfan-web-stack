#!/usr/bin/env bash
# Install/update only vote.billfan.cn. Invoke from a trusted checkout as root.
set -Eeuo pipefail
umask 077

SOURCE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
INSTALL_ROOT=/opt/dankou-vote
DATA_DIR=/var/lib/dankou-vote
CONFIG_DIR=/etc/dankou-vote
ENV_FILE="$CONFIG_DIR/vote.env"
SERVICE_FILE=/etc/systemd/system/dankou-vote.service
NGINX_FILE=/etc/nginx/conf.d/vote.billfan.cn.conf
DOMAIN=vote.billfan.cn
ACME_EMAIL="${ACME_EMAIL:-}"
STAMP="$(date -u +%Y%m%dT%H%M%S)-$$"
RELEASE="$INSTALL_ROOT/releases/$STAMP"
BACKUP_DIR="/var/backups/dankou-vote/$STAMP"
ORIGINAL_CURRENT=""
SERVICE_WAS_ACTIVE=0
SERVICE_WAS_ENABLED=0
CONFIG_CHANGED=0
SERVICE_CHANGED=0
SWITCHED=0

log() { printf '[dankou-vote] %s\n' "$*"; }
fail() { printf '[dankou-vote] ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'USAGE'
Usage: sudo bash scripts/deploy/deploy_vote.sh [--email ACME_EMAIL]

The first install generates and retains local administrator credentials.
The optional email receives certificate expiry notices. Without it, certbot
registers without an email. DNS for vote.billfan.cn must point to this server.
This script never resets votes, rotates existing keys, or restarts other sites.
USAGE
}

while (($#)); do
    case "$1" in
        --email)
            (($# >= 2)) || fail '--email needs a value'
            ACME_EMAIL="$2"
            shift 2
            ;;
        -h|--help) usage; exit 0 ;;
        *) fail "Unknown argument: $1" ;;
    esac
done

[[ "$(id -u)" == 0 ]] || fail 'Run with sudo bash scripts/deploy/deploy_vote.sh'
for cmd in python3 nginx systemctl curl flock install cp mv ln useradd getent; do
    command -v "$cmd" >/dev/null || fail "Missing dependency: $cmd"
done
python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit('Python 3.10 or newer is required.')
PY
[[ -f "$SOURCE_ROOT/services/vote/app.py" ]] || fail 'The checkout is missing services/vote/app.py'
[[ -f "$SOURCE_ROOT/services/vote/static/index.html" ]] || fail 'The checkout is missing the frontend'
[[ -f "$SOURCE_ROOT/services/vote/static/players.html" ]] || fail 'The checkout is missing players.html'
[[ -f "$SOURCE_ROOT/services/vote/static/admin.html" ]] || fail 'The checkout is missing admin.html'
[[ -f "$SOURCE_ROOT/services/vote/requirements.txt" ]] || fail 'The checkout is missing requirements.txt'
[[ ! -e "$INSTALL_ROOT/current" || -L "$INSTALL_ROOT/current" ]] || fail "$INSTALL_ROOT/current must be a symlink"
[[ ! -e "$NGINX_FILE" || -f "$NGINX_FILE" ]] || fail "$NGINX_FILE must be a regular config file"
nginx -t

exec 9>/run/lock/dankou-vote-deploy.lock
flock -n 9 || fail 'Another vote deploy is running'

if [[ -L "$INSTALL_ROOT/current" ]]; then
    ORIGINAL_CURRENT="$(readlink -f "$INSTALL_ROOT/current")"
    [[ "$ORIGINAL_CURRENT" == "$INSTALL_ROOT/releases/"* ]] || fail 'Existing release symlink has an unexpected target'
fi
systemctl is-active --quiet dankou-vote && SERVICE_WAS_ACTIVE=1
systemctl is-enabled --quiet dankou-vote 2>/dev/null && SERVICE_WAS_ENABLED=1
if ((!SERVICE_WAS_ACTIVE)); then
    python3 - <<'PY'
import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        listener.bind(('127.0.0.1', 8020))
    except OSError as error:
        raise SystemExit('Port 8020 is occupied while dankou-vote is inactive. Resolve the existing listener before deploying.') from error
PY
fi

install -d -m 0755 "$INSTALL_ROOT" "$INSTALL_ROOT/releases" /var/www/certbot
install -d -m 0700 "$CONFIG_DIR" "$BACKUP_DIR"
for item in "$NGINX_FILE" "$SERVICE_FILE"; do
    if [[ -f "$item" ]]; then
        cp -a -- "$item" "$BACKUP_DIR/$(basename -- "$item")"
    fi
done
printf '%s\n' "$ORIGINAL_CURRENT" > "$BACKUP_DIR/previous-release.txt"

rollback_on_error() {
    local rc=$?
    trap - EXIT ERR INT TERM
    ((rc != 0)) || return 0
    set +e
    log "Deploy failed (exit $rc); restoring previous code and site configuration."
    if ((SWITCHED)); then
        if [[ -n "$ORIGINAL_CURRENT" ]]; then
            ln -s "$ORIGINAL_CURRENT" "$INSTALL_ROOT/.rollback-$STAMP"
            mv -Tf "$INSTALL_ROOT/.rollback-$STAMP" "$INSTALL_ROOT/current"
        elif [[ -L "$INSTALL_ROOT/current" ]]; then
            rm -- "$INSTALL_ROOT/current"
        fi
    fi
    if ((SERVICE_CHANGED)); then
        if [[ -f "$BACKUP_DIR/dankou-vote.service" ]]; then
            cp -a "$BACKUP_DIR/dankou-vote.service" "$SERVICE_FILE"
        else
            systemctl stop dankou-vote >/dev/null 2>&1
            systemctl disable dankou-vote >/dev/null 2>&1
            rm -f -- "$SERVICE_FILE"
        fi
        systemctl daemon-reload
        if ((SERVICE_WAS_ACTIVE)); then
            systemctl restart dankou-vote
        else
            systemctl stop dankou-vote >/dev/null 2>&1
        fi
        if ((!SERVICE_WAS_ENABLED)); then
            systemctl disable dankou-vote >/dev/null 2>&1
        fi
    fi
    if ((CONFIG_CHANGED)); then
        if [[ -f "$BACKUP_DIR/vote.billfan.cn.conf" ]]; then
            cp -a "$BACKUP_DIR/vote.billfan.cn.conf" "$NGINX_FILE"
        else
            rm -f -- "$NGINX_FILE"
        fi
        if nginx -t; then
            systemctl reload nginx
        else
            log 'nginx configuration is invalid; existing nginx workers were left running. Inspect configuration manually.'
        fi
    fi
    log "Persistent votes and credentials were retained. Diagnostic backup: $BACKUP_DIR"
    exit "$rc"
}
trap rollback_on_error EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if ! getent passwd dankou-vote >/dev/null; then
    useradd --system --user-group --home-dir "$DATA_DIR" --shell /usr/sbin/nologin dankou-vote
fi
install -d -o dankou-vote -g dankou-vote -m 0700 "$DATA_DIR"

# Exclusive create: reruns keep both secrets and all existing settings unchanged.
python3 - "$ENV_FILE" <<'PY'
import os, secrets, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.exists():
    values = {
        'VOTE_DB_PATH': '/var/lib/dankou-vote/vote.sqlite3',
        'VOTE_ADMIN_PASSWORD': secrets.token_urlsafe(24),
        'VOTE_SECRET_KEY': secrets.token_urlsafe(48),
        'VOTE_COOKIE_SECURE': 'true',
        'VOTE_ALLOWED_ORIGINS': 'https://vote.billfan.cn',
        'VOTE_FINGERPRINT_RECOVERY': 'true',
        'VOTE_VOTE_INTERVAL_MS': '800',
        'VOTE_MESSAGE_INTERVAL_MS': '5000',
    }
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(''.join(f'{k}={v}\n' for k, v in values.items()))
        f.flush()
        os.fsync(f.fileno())
settings = {}
for line in p.read_text().splitlines():
    if line.strip() and not line.lstrip().startswith('#'):
        key, sep, value = line.partition('=')
        if sep:
            settings[key.strip()] = value.strip().strip('"').strip("'")
for key, minimum in [('VOTE_ADMIN_PASSWORD', 16), ('VOTE_SECRET_KEY', 32)]:
    value = settings.get(key, '')
    if len(value) < minimum or 'REPLACE_' in value or '\n' in value:
        raise SystemExit(f'{key} is missing or still a placeholder in {p}; update it locally.')
if settings.get('VOTE_DB_PATH') != '/var/lib/dankou-vote/vote.sqlite3':
    raise SystemExit('This installer expects VOTE_DB_PATH=/var/lib/dankou-vote/vote.sqlite3.')
if settings.get('VOTE_COOKIE_SECURE', '').lower() not in ('true', '1', 'yes'):
    raise SystemExit('The production installer requires VOTE_COOKIE_SECURE=true.')
os.chmod(p, 0o600)
PY

log 'Preparing an isolated release and Python environment.'
install -d -m 0755 "$RELEASE/services"
python3 - "$SOURCE_ROOT/services/vote" "$RELEASE/services/vote" <<'PY'
import shutil, sys
shutil.copytree(sys.argv[1], sys.argv[2], ignore=shutil.ignore_patterns(
    '__pycache__', '.venv', '.env', '.env.*', '*.sqlite*', '*.db', '.pytest_cache'
))
PY
chmod -R a+rX "$RELEASE"
python3 -m venv "$RELEASE/.venv"
"$RELEASE/.venv/bin/python" -m pip install --disable-pip-version-check -r "$RELEASE/services/vote/requirements.txt"
"$RELEASE/.venv/bin/python" -m compileall -q "$RELEASE/services/vote"
chmod -R a+rX "$RELEASE"

# SQLite's online backup API includes committed WAL contents in a consistent copy.
if [[ -f "$DATA_DIR/vote.sqlite3" ]]; then
    log 'Taking a consistent database backup before updating.'
    python3 - "$DATA_DIR/vote.sqlite3" "$BACKUP_DIR/vote.sqlite3" <<'PY'
import os, pwd, sqlite3, stat, sys
from contextlib import closing
from pathlib import Path
source = Path(sys.argv[1])
owner = pwd.getpwnam('dankou-vote')
state_paths = [Path(str(source) + suffix) for suffix in ('', '-wal', '-shm', '.lock')]
for path in state_paths:
    if path.exists() or path.is_symlink():
        if not stat.S_ISREG(path.lstat().st_mode):
            raise SystemExit(f'Expected a regular database state file: {path}')
try:
    with closing(sqlite3.connect(f'file:{source}?mode=ro', uri=True, timeout=30)) as src:
        with closing(sqlite3.connect(sys.argv[2])) as dst:
            src.backup(dst)
finally:
    # A root read-only WAL connection can still create -wal/-shm sidecars.
    # Keep them usable by the dedicated account, including after a failed backup.
    for path in state_paths:
        try:
            current = path.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(current.st_mode):
            raise SystemExit(f'Unexpected database state path: {path}')
        os.chown(path, owner.pw_uid, owner.pw_gid, follow_symlinks=False)
PY
fi

if [[ ! -s "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" || ! -s "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]]; then
    command -v certbot >/dev/null || fail 'Install certbot first (Debian/Ubuntu: apt-get install certbot).'
    log 'Installing the temporary ACME-only vhost and requesting the certificate.'
    CONFIG_CHANGED=1
    install -m 0644 "$SOURCE_ROOT/deploy/nginx/vote.billfan.cn.http.conf" "$NGINX_FILE"
    nginx -t
    systemctl reload nginx
    cert_args=(certonly --webroot --webroot-path /var/www/certbot --domain "$DOMAIN" --non-interactive --agree-tos)
    if [[ -n "$ACME_EMAIL" ]]; then
        cert_args+=(--email "$ACME_EMAIL")
    else
        cert_args+=(--register-unsafely-without-email)
    fi
    certbot "${cert_args[@]}"
fi

log 'Switching the vote service to the prepared release.'
ln -s "$RELEASE" "$INSTALL_ROOT/.current-$STAMP"
mv -Tf "$INSTALL_ROOT/.current-$STAMP" "$INSTALL_ROOT/current"
SWITCHED=1
SERVICE_CHANGED=1
install -m 0644 "$SOURCE_ROOT/deploy/systemd/dankou-vote.service" "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable dankou-vote >/dev/null
systemctl restart dankou-vote

healthy=0
for attempt in $(seq 1 20); do
    if curl --fail --silent --max-time 2 http://127.0.0.1:8020/api/health | python3 -c 'import json,sys; value=json.load(sys.stdin); sys.exit(0 if value.get("ok") is True and value.get("service")=="dankou-vote" else 1)' 2>/dev/null; then
        healthy=1
        break
    fi
    sleep 0.5
done
((healthy)) || fail 'The vote backend did not become healthy; inspect journalctl -u dankou-vote.'
systemctl is-active --quiet dankou-vote || fail 'The vote process exited during startup; check whether port 8020 is already occupied.'

CONFIG_CHANGED=1
install -m 0644 "$SOURCE_ROOT/deploy/nginx/vote.billfan.cn.conf" "$NGINX_FILE"
nginx -t
systemctl reload nginx
# --resolve verifies this host, certificate, vhost, static pages, and reverse proxy.
curl --fail --silent --show-error --max-time 10 --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/api/health" | python3 -c 'import json,sys; value=json.load(sys.stdin); sys.exit(0 if value.get("ok") is True and value.get("service")=="dankou-vote" else 1)'
for page in / /players /admin; do
    curl --fail --silent --show-error --max-time 10 --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN$page" >/dev/null
done

# Do not print the administrator credential into terminal or CI logs.
python3 - "$ENV_FILE" "$CONFIG_DIR/admin-url.txt" <<'PY'
import os, sys
from pathlib import Path
from urllib.parse import quote
values = {}
for line in Path(sys.argv[1]).read_text().splitlines():
    if line.strip() and not line.lstrip().startswith('#'):
        key, sep, value = line.partition('=')
        if sep:
            values[key.strip()] = value.strip().strip('"').strip("'")
url = 'https://vote.billfan.cn/admin#key=' + quote(values['VOTE_ADMIN_PASSWORD'], safe='') + '\n'
fd = os.open(sys.argv[2], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write(url)
os.chmod(sys.argv[2], 0o600)
PY
if [[ -n "$ORIGINAL_CURRENT" ]]; then
    ln -s "$ORIGINAL_CURRENT" "$INSTALL_ROOT/.previous-$STAMP"
    mv -Tf "$INSTALL_ROOT/.previous-$STAMP" "$INSTALL_ROOT/previous"
fi
trap - EXIT ERR INT TERM
log "Ready: https://$DOMAIN"
log "Release: $RELEASE"
log "Previous configuration and database snapshot: $BACKUP_DIR"
log 'Administrator URL is in /etc/dankou-vote/admin-url.txt (root-readable only).'
log 'Read it privately with: sudo cat /etc/dankou-vote/admin-url.txt'
log 'Verify again with: sudo bash scripts/deploy/verify_vote.sh'
log 'Ensure certbot renewal is scheduled; certificate renewal must reload nginx.'
