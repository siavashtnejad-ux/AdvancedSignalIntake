#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/advanced-signal-intake
REPO_URL=https://github.com/siavashtnejad-ux/AdvancedSignalIntake.git
SERVICE_NAME=advanced-signal-intake

if [ "${EUID}" -ne 0 ]; then
  echo "Run this script with sudo/root." >&2
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git python3 python3-venv python3-pip nginx curl

if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" pull --ff-only
fi

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip wheel
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

mkdir -p "$APP_DIR/data"
chown -R www-data:www-data "$APP_DIR/data"
chmod 750 "$APP_DIR/data"

if [ ! -f /etc/advanced-signal-intake.env ]; then
  cp "$APP_DIR/server/advanced-signal-intake.env.example" /etc/advanced-signal-intake.env
  chmod 600 /etc/advanced-signal-intake.env
  echo
  echo "Created /etc/advanced-signal-intake.env"
  echo "Edit it before enabling external APIs that need contact info or keys."
fi

cp "$APP_DIR/server/advanced-signal-intake.service" /etc/systemd/system/advanced-signal-intake.service
systemctl daemon-reload
systemctl enable --now advanced-signal-intake

sleep 2
curl -fsS http://127.0.0.1:8081/api/health >/dev/null

echo
printf '%s\n' "Backend is healthy on 127.0.0.1:8081." 
printf '%s\n' "Next: add server/nginx-signals-location.conf inside your EXISTING Nginx server block, then run:" 
printf '%s\n' "  nginx -t && systemctl reload nginx"
printf '%s\n' "Public URL will be: http://85.198.17.18/signals/"
