#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/advanced-signal-intake
REPO_URL=https://github.com/siavashtnejad-ux/AdvancedSignalIntake.git

if [ "${EUID}" -ne 0 ]; then
  echo "Run this script with sudo/root." >&2
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git curl docker.io docker-compose
systemctl enable --now docker

if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" pull --ff-only
fi

cd "$APP_DIR"
mkdir -p data

if [ ! -f .env ]; then
  cp server/advanced-signal-intake.env.example .env
  chmod 600 .env
  echo
  echo "Created $APP_DIR/.env"
  echo "Edit this file later to add NCBI_EMAIL, OPENALEX_API_KEY, and CROSSREF_MAILTO."
fi

# Docker Compose v1 is available in Ubuntu 20.04 repositories.
docker-compose -f docker-compose.ip.yml up -d --build

for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8081/api/health >/dev/null 2>&1; then
    echo
    echo "AdvancedSignalIntake backend is healthy on 127.0.0.1:8081."
    echo "Now add server/nginx-signals-location.conf INSIDE your existing Nginx server block."
    echo "Then run: nginx -t && systemctl reload nginx"
    echo "Public URL: http://85.198.17.18/signals/"
    exit 0
  fi
  sleep 2
done

echo "Container started but health check did not succeed in time." >&2
docker-compose -f docker-compose.ip.yml ps
docker-compose -f docker-compose.ip.yml logs --tail=100 app
exit 1
