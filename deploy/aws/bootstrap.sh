#!/usr/bin/env bash
# Provision a fresh Ubuntu 24.04 EC2 instance to run Archivist.
#
#   sudo ./deploy/aws/bootstrap.sh [domain]
#
# Installs Docker, nginx and certbot, prepares storage and swap, then builds
# and starts the app. Safe to re-run; each step is idempotent.
#
# Prerequisites:
#   - Instance with at least 4 GB RAM (t3.medium) and a 30 GB root volume.
#     The image is ~3.1 GB and the build needs room for layers; the 8 GB
#     default will run out of disk.
#   - Security group allowing inbound 22, 80 and 443 only. The app itself is
#     bound to loopback and is not reachable directly.
#   - deploy/aws/.env filled in from .env.example.
set -euo pipefail

DOMAIN="${1:-}"
REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DATA_DIR=/srv/archivist/data

if [ "$(id -u)" -ne 0 ]; then
    echo "FATAL: run with sudo." >&2
    exit 1
fi

if [ ! -f "$REPO_DIR/deploy/aws/.env" ]; then
    echo "FATAL: deploy/aws/.env is missing." >&2
    echo "Copy deploy/aws/.env.example to deploy/aws/.env and fill in DB_URL and GROQ_API_KEY." >&2
    exit 1
fi

echo "==> Installing packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg nginx

if ! command -v docker >/dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
systemctl enable --now docker

# A 4 GB instance loading two models has little headroom; swap turns a hard
# OOM kill during startup into a slow start.
if [ ! -f /swapfile ]; then
    echo "==> Creating 2 GB swap"
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap -q /swapfile
    swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# The container runs as UID 1000 and cannot write a root-owned directory; the
# entrypoint would fall back to ephemeral storage and quietly lose uploads.
echo "==> Preparing $DATA_DIR"
mkdir -p "$DATA_DIR"
chown -R 1000:1000 "$DATA_DIR"

echo "==> Building and starting the app (first build takes 10-15 minutes)"
cd "$REPO_DIR/deploy/aws"
docker compose up -d --build

if [ -n "$DOMAIN" ]; then
    echo "==> Configuring nginx for $DOMAIN"
    sed "s/REPLACE_WITH_DOMAIN/$DOMAIN/" "$REPO_DIR/deploy/aws/nginx.conf" \
        > /etc/nginx/sites-available/archivist
    ln -sf /etc/nginx/sites-available/archivist /etc/nginx/sites-enabled/archivist
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl reload nginx

    echo "==> Requesting a certificate"
    apt-get install -y -qq certbot python3-certbot-nginx
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
        --register-unsafely-without-email --redirect
    echo "==> https://$DOMAIN"
else
    echo "==> No domain given; nginx not configured."
    echo "==> Re-run with a domain once DNS points at this instance:"
    echo "==>   sudo $0 example.com"
    echo "==> Until then the app is on loopback only. Check it with:"
    echo "==>   curl -I http://127.0.0.1:7860/login"
fi

echo "==> Done. Logs: docker compose -f $REPO_DIR/deploy/aws/docker-compose.yml logs -f"
