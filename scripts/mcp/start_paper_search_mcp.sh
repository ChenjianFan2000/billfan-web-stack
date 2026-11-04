#!/usr/bin/env bash
set -euo pipefail

PAPER_SEARCH_DIR="${PAPER_SEARCH_DIR:-/var/www/services/paper-search-mcp}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. run scripts/mcp/setup_mcp.sh first." >&2
  exit 1
fi

exec uv run --directory "$PAPER_SEARCH_DIR" -m paper_search_mcp.server
