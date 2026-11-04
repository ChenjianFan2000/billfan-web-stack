#!/usr/bin/env bash
# Build frontend and launch single-process production server at :8000.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"

cd "$ROOT/frontend"
npm run build

if [ -f "$ROOT/.env" ]; then
  set -a
  . "$ROOT/.env"
  set +a
fi

cd "$REPO_ROOT"
python -m uvicorn paper_visualizer.backend.api:app --host 127.0.0.1 --port 8000
