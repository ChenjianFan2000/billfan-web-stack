#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-/var/www}"
PAPER_SEARCH_DIR="${PAPER_SEARCH_DIR:-$ROOT_DIR/services/paper-search-mcp}"
EXA_MCP_URL="${EXA_MCP_URL:-https://mcp.exa.ai/mcp}"
SKIP_PAPER_SYNC="${SKIP_PAPER_SYNC:-0}"
REPLACE_EXISTING_MCP="${REPLACE_EXISTING_MCP:-1}"
UV_PYTHON_VERSION="${UV_PYTHON_VERSION:-3.12}"

log() {
  printf "[setup_mcp] %s\n" "$*"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "missing command: $1"
    return 1
  fi
}

install_uv_if_needed() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi
  log "uv not found, installing via official script"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  need_cmd uv
}

fetch_paper_search_repo() {
  mkdir -p "$(dirname "$PAPER_SEARCH_DIR")"

  if [ -d "$PAPER_SEARCH_DIR/.git" ] && command -v git >/dev/null 2>&1; then
    log "updating existing paper-search-mcp repo"
    git -C "$PAPER_SEARCH_DIR" pull --ff-only
    return
  fi

  if [ -d "$PAPER_SEARCH_DIR" ] && [ "$(ls -A "$PAPER_SEARCH_DIR" 2>/dev/null)" != "" ]; then
    log "using existing non-git directory: $PAPER_SEARCH_DIR"
    return
  fi

  if command -v git >/dev/null 2>&1; then
    log "cloning openags/paper-search-mcp"
    git clone https://github.com/openags/paper-search-mcp.git "$PAPER_SEARCH_DIR"
    return
  fi

  log "git not found, downloading tarball from GitHub"
  tmp_dir="$(mktemp -d)"
  curl -fsSL https://github.com/openags/paper-search-mcp/archive/refs/heads/main.tar.gz \
    | tar -xzf - -C "$tmp_dir"
  mv "$tmp_dir/paper-search-mcp-main" "$PAPER_SEARCH_DIR"
  rmdir "$tmp_dir"
}

upsert_mcp_server() {
  local name="$1"
  shift

  if codex mcp get "$name" >/dev/null 2>&1; then
    if [ "$REPLACE_EXISTING_MCP" = "1" ]; then
      log "removing existing MCP server: $name"
      codex mcp remove "$name"
    else
      log "MCP server already exists, skip: $name"
      return
    fi
  fi

  codex mcp add "$name" "$@"
}

register_exa_mcp() {
  log "registering Exa MCP: $EXA_MCP_URL"
  upsert_mcp_server exa --url "$EXA_MCP_URL"
}

register_paper_search_mcp() {
  if [ -n "${SEMANTIC_SCHOLAR_API_KEY:-}" ]; then
    log "registering paper_search MCP with SEMANTIC_SCHOLAR_API_KEY"
    upsert_mcp_server paper_search \
      --env "SEMANTIC_SCHOLAR_API_KEY=${SEMANTIC_SCHOLAR_API_KEY}" \
      -- uv run --directory "$PAPER_SEARCH_DIR" -m paper_search_mcp.server
  else
    log "registering paper_search MCP without SEMANTIC_SCHOLAR_API_KEY"
    upsert_mcp_server paper_search \
      -- uv run --directory "$PAPER_SEARCH_DIR" -m paper_search_mcp.server
  fi
}

main() {
  need_cmd codex
  need_cmd curl

  install_uv_if_needed
  fetch_paper_search_repo

  if [ "$SKIP_PAPER_SYNC" = "1" ]; then
    log "skip dependency sync (SKIP_PAPER_SYNC=1)"
  else
    log "syncing Python dependencies for paper-search-mcp (Python $UV_PYTHON_VERSION)"
    uv sync --directory "$PAPER_SEARCH_DIR" --python "$UV_PYTHON_VERSION"
  fi

  register_exa_mcp
  register_paper_search_mcp

  log "done. current MCP list:"
  codex mcp list
}

main "$@"
