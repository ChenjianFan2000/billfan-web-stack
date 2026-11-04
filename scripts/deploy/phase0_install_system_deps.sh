#!/usr/bin/env bash
set -euo pipefail

log() {
  printf "[phase0/install] %s\n" "$*"
}

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "please run as root" >&2
    exit 1
  fi
}

install_with_apt() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    pkg-config \
    curl
}

install_with_dnf() {
  dnf makecache
  dnf install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    python3 \
    python3-pip \
    gcc \
    gcc-c++ \
    make \
    rust \
    cargo \
    libxml2-devel \
    libxslt-devel \
    pkgconf-pkg-config \
    curl
}

install_with_yum() {
  yum makecache
  yum install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    python3 \
    python3-pip \
    gcc \
    gcc-c++ \
    make \
    rust \
    cargo \
    libxml2-devel \
    libxslt-devel \
    pkgconf-pkg-config \
    curl
}

install_uv_if_needed() {
  if command -v uv >/dev/null 2>&1; then
    log "uv already installed"
    return
  fi

  log "installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  if [ -f "$HOME/.local/bin/env" ]; then
    # shellcheck source=/dev/null
    source "$HOME/.local/bin/env"
  fi
}

main() {
  require_root

  if command -v apt-get >/dev/null 2>&1; then
    log "detected apt-based system"
    install_with_apt
  elif command -v dnf >/dev/null 2>&1; then
    log "detected dnf-based system"
    install_with_dnf
  elif command -v yum >/dev/null 2>&1; then
    log "detected yum-based system"
    install_with_yum
  else
    echo "unsupported package manager" >&2
    exit 1
  fi

  install_uv_if_needed

  systemctl enable nginx
  systemctl start nginx
  log "system dependencies installed"
}

main "$@"
