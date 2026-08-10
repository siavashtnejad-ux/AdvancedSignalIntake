#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install Docker Engine + Compose plugin first."
  exit 1
fi

if [ ! -f .env ]; then
  echo ".env not found. Copy .env.production.example to .env and edit it first."
  exit 1
fi

mkdir -p data backups

echo "Pulling latest code..."
git pull --ff-only

echo "Building and starting production stack..."
docker compose up -d --build

echo "Waiting for application health..."
for i in $(seq 1 30); do
  if docker compose exec -T app curl -fsS http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
    echo "Application is healthy."
    docker compose ps
    exit 0
  fi
  sleep 2
done

echo "Application did not become healthy in time. Recent logs:"
docker compose logs --tail=100 app caddy
exit 1
