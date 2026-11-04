#!/usr/bin/env bash
# Launch backend (:8000) and frontend (:5173) dev servers.
# Frontend proxies /api → backend.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"

if [ -f "$ROOT/.env" ]; then
  set -a
  . "$ROOT/.env"
  set +a
else
  echo "Warning: $ROOT/.env not found. AI features will not work." >&2
fi

cleanup() {
  if [[ -n "${BACK_PID:-}" ]] && kill -0 "$BACK_PID" 2>/dev/null; then
    kill "$BACK_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

cd "$REPO_ROOT"
python -m uvicorn paper_visualizer.backend.api:app --host 127.0.0.1 --port 8000 --reload &
BACK_PID=$!

cd "$ROOT/frontend"
npm run dev
