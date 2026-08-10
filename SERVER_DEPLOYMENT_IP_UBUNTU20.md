# AdvancedSignalIntake on Ubuntu 20.04 + Existing Nginx

Target public URL:

```text
http://85.198.17.18/signals/
```

The existing website on port 80 remains untouched except for adding a dedicated `/signals/` location.

## Architecture

```text
Internet
  |
  v
Existing Nginx :80
  |-- /                 -> existing website
  |-- /signals/         -> 127.0.0.1:8081
                              |
                              v
                         Docker container
                         FastAPI :8080
                              |
                              +-- frontend
                              +-- SQLite
                              +-- PubMed
                              +-- ClinicalTrials.gov
                              +-- OpenAlex
                              +-- Crossref
```

## 1. SSH to the server

```bash
ssh YOUR_USER@85.198.17.18
```

Do not share SSH passwords or private keys in chat.

## 2. Install and start the application

```bash
cd /tmp
git clone https://github.com/siavashtnejad-ux/AdvancedSignalIntake.git
cd AdvancedSignalIntake
sudo bash scripts/install-ubuntu20-nginx.sh
```

The script installs Docker from Ubuntu repositories, clones the production copy into:

```text
/opt/advanced-signal-intake
```

and starts FastAPI only on:

```text
127.0.0.1:8081
```

It does **not** expose port 8081 to the Internet.

## 3. Verify backend before touching Nginx

```bash
curl http://127.0.0.1:8081/api/health
```

Expected JSON contains:

```json
{"ok": true}
```

Check container state:

```bash
cd /opt/advanced-signal-intake
sudo docker-compose -f docker-compose.ip.yml ps
sudo docker-compose -f docker-compose.ip.yml logs --tail=100 app
```

## 4. Locate the existing Nginx site

```bash
sudo ls -l /etc/nginx/sites-enabled/
sudo nginx -T 2>/dev/null | grep -nE 'listen 80|server_name'
```

Open the configuration file that contains the active `server { ... }` block for the current website.

Before changing it, back it up:

```bash
sudo cp /etc/nginx/sites-available/YOUR_SITE /etc/nginx/sites-available/YOUR_SITE.backup
```

## 5. Add the `/signals/` reverse proxy

Inside the existing `server { ... }` block, add the content from:

```text
/opt/advanced-signal-intake/server/nginx-signals-location.conf
```

You can display it with:

```bash
cat /opt/advanced-signal-intake/server/nginx-signals-location.conf
```

Do not create a second `listen 80` server unless you know your current Nginx layout requires it.

## 6. Validate Nginx before reload

```bash
sudo nginx -t
```

Only if the test succeeds:

```bash
sudo systemctl reload nginx
```

## 7. Test public site

```bash
curl -I http://85.198.17.18/signals/
curl http://85.198.17.18/signals/api/health
```

Open in a browser:

```text
http://85.198.17.18/signals/
```

FastAPI API documentation:

```text
http://85.198.17.18/signals/docs
```

## 8. Configure external research APIs

Edit:

```bash
sudo nano /opt/advanced-signal-intake/.env
```

Recommended values:

```env
NCBI_EMAIL=your-email@example.org
NCBI_API_KEY=
OPENALEX_API_KEY=YOUR_OPENALEX_KEY
CROSSREF_MAILTO=your-email@example.org
```

Do not commit this file to GitHub.

After changing `.env`:

```bash
cd /opt/advanced-signal-intake
sudo docker-compose -f docker-compose.ip.yml up -d --build
```

## 9. Updates

```bash
cd /opt/advanced-signal-intake
sudo git pull --ff-only
sudo docker-compose -f docker-compose.ip.yml up -d --build
```

## 10. SQLite data

Persistent database:

```text
/opt/advanced-signal-intake/data/ethical_horizon.db
```

The database directory is mounted into the container, so rebuilding the container does not erase scans.

## 11. Security

- Keep port `8081` bound to `127.0.0.1` only.
- Do not open port 8081 in UFW/security groups.
- Never put `.env`, API keys, SSH private keys, or passwords in GitHub.
- This IP-only deployment is HTTP. A normal trusted HTTPS setup is best added after assigning a domain/subdomain.
