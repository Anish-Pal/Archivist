#!/usr/bin/env bash
# Provision a fresh Ubuntu 24.04 EC2 instance to run Archivist.
#
#   sudo ./deploy/aws/bootstrap.sh [quick|named]
#
# Installs Docker, prepares storage and swap, builds the image and starts the
# app behind a Cloudflare Tunnel. Safe to re-run; every step is idempotent.
#
# Profiles:
#   quick  (default) Cloudflare allocates a random *.trycloudflare.com URL.
#                    No domain, no certificates, no inbound ports. The URL
#                    changes every time the tunnel restarts.
#   named            Stable hostname on a Cloudflare-managed domain. Requires
#                    CLOUDFLARE_TUNNEL_TOKEN in .env.
#
# Prerequisites:
#   - At least 4 GB RAM (t3.medium) and a 30 GB root volume. The image is
#     ~3.1 GB and the build needs room for layers; the 8 GB default runs out.
#   - Security group allowing inbound 22 only. The tunnel dials out, so no
#     inbound 80/443 is needed.
#   - deploy/aws/.env filled in from .env.example.
set -euo pipefail

PROFILE="${1:-quick}"
REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="$REPO_DIR/deploy/aws/.env"
DATA_DIR=/srv/archivist/data

if [ "$(id -u)" -ne 0 ]; then
    echo "FATAL: run with sudo." >&2
    exit 1
fi

case "$PROFILE" in
    quick|named) ;;
    *) echo "FATAL: profile must be 'quick' or 'named', got '$PROFILE'." >&2; exit 1 ;;
esac

if [ ! -f "$ENV_FILE" ]; then
    echo "FATAL: deploy/aws/.env is missing." >&2
    echo "Copy deploy/aws/.env.example to deploy/aws/.env and fill in DB_URL and GROQ_API_KEY." >&2
    exit 1
fi

for required in DB_URL GROQ_API_KEY; do
    if ! grep -qE "^${required}=.+" "$ENV_FILE"; then
        echo "FATAL: $required is empty in deploy/aws/.env." >&2
        exit 1
    fi
done

if [ "$PROFILE" = "named" ] && ! grep -qE '^CLOUDFLARE_TUNNEL_TOKEN=.+' "$ENV_FILE"; then
    echo "FATAL: the 'named' profile needs CLOUDFLARE_TUNNEL_TOKEN in deploy/aws/.env." >&2
    echo "Create the tunnel in the Cloudflare Zero Trust dashboard, point it at" >&2
    echo "http://app:7860, and paste its token." >&2
    exit 1
fi

echo "==> Installing Docker"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg

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

echo "==> Building and starting (first build takes 10-15 minutes)"
cd "$REPO_DIR/deploy/aws"
docker compose --profile "$PROFILE" up -d --build

echo "==> Waiting for the app to finish loading models"
for _ in $(seq 1 60); do
    if curl -fsS -o /dev/null http://127.0.0.1:7860/login 2>/dev/null; then
        echo "==> App is serving"
        break
    fi
    sleep 10
done

if [ "$PROFILE" = "quick" ]; then
    echo "==> Public URL (also in: docker compose logs tunnel-quick)"
    for _ in $(seq 1 30); do
        url=$(docker compose --profile quick logs tunnel-quick 2>/dev/null \
              | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1)
        if [ -n "$url" ]; then
            echo "==>"
            echo "==>   $url"
            echo "==>"
            echo "==> This URL changes whenever the tunnel restarts. For a stable"
            echo "==> hostname, use the 'named' profile with a Cloudflare domain."
            break
        fi
        sleep 5
    done
    [ -n "${url:-}" ] || echo "==> Tunnel URL not visible yet; check the logs."
else
    echo "==> Tunnel running. The hostname is the one configured in Cloudflare."
fi

echo "==> Logs: docker compose -f $REPO_DIR/deploy/aws/docker-compose.yml --profile $PROFILE logs -f"
