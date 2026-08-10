# AdvancedSignalIntake — Production Server Deployment

This guide deploys the full FastAPI + SQLite application behind Caddy with automatic HTTPS.

## Assumptions

- Ubuntu/Debian-class VPS with a public IP
- A domain/subdomain points to the server with an A/AAAA DNS record
- TCP ports 80 and 443 are open
- Docker Engine and Docker Compose plugin are installed

## 1. Clone

```bash
sudo mkdir -p /opt/advanced-signal-intake
sudo chown "$USER":"$USER" /opt/advanced-signal-intake
git clone https://github.com/siavashtnejad-ux/AdvancedSignalIntake.git /opt/advanced-signal-intake
cd /opt/advanced-signal-intake
```

## 2. Configure environment

```bash
cp .env.production.example .env
nano .env
```

At minimum configure:

```env
DOMAIN=signal.example.com
ACME_EMAIL=admin@example.com
NCBI_EMAIL=researcher@example.com
OPENALEX_API_KEY=your_key_here
CROSSREF_MAILTO=researcher@example.com
```

Do not commit `.env`.

## 3. Start

```bash
bash scripts/deploy.sh
```

Check:

```bash
docker compose ps
docker compose logs -f --tail=100 app caddy
```

Application health from the server:

```bash
curl -fsS http://127.0.0.1:8080/api/health
```

Public health through Caddy:

```bash
curl -fsS https://YOUR_DOMAIN/api/health
```

## 4. Update later

```bash
cd /opt/advanced-signal-intake
bash scripts/deploy.sh
```

## 5. Backup SQLite

```bash
cd /opt/advanced-signal-intake
python3 scripts/backup_db.py
```

For a daily cron job:

```cron
15 3 * * * cd /opt/advanced-signal-intake && /usr/bin/python3 scripts/backup_db.py >> /var/log/advanced-signal-backup.log 2>&1
```

## 6. Firewall example (UFW)

Keep SSH allowed before enabling the firewall.

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Architecture

```text
Internet
   |
   v
Caddy :80/:443
   |
   v
FastAPI/Uvicorn :8080
   |
   +-- frontend/
   +-- /api/*
   +-- SQLite /app/data/ethical_horizon.db
   +-- PubMed
   +-- ClinicalTrials.gov
   +-- OpenAlex
   +-- Crossref
```

The SQLite database is persisted through the host directory `./data` mounted into `/app/data` in the application container.

## Security notes

- Never publish `.env`, API keys, SSH keys, or server passwords.
- Prefer SSH key authentication and disable password login after confirming key access.
- Keep Docker and the OS security updates current.
- Restrict direct access to port 8080; it is intentionally only exposed to the internal Docker network.
- HTTPS is terminated by Caddy.
