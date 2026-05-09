# Ghost CFO — Production Deployment Guide

Numbers10 VPS: Hetzner Ubuntu 24 LTS  
Domain: `ghostcfo.numbers10.co.za`  
Repo: `github.com/Joevikingroux/ghostgfo`

---

## First-time VPS setup

```bash
# 1. Install Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
apt-get install -y nginx certbot python3-certbot-nginx

# 2. Clone the repo
mkdir -p /opt/ghostcfo && cd /opt/ghostcfo
git clone https://github.com/Joevikingroux/ghostgfo.git .

# 3. Create .env from the example
cp .env.example .env
nano .env   # fill in all secrets

# 4. Add rate-limit zones to /etc/nginx/nginx.conf (inside http {} block)
#    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
#    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

# 5. Install the nginx site config
cp nginx/nginx.conf /etc/nginx/sites-available/ghostcfo
ln -s /etc/nginx/sites-available/ghostcfo /etc/nginx/sites-enabled/ghostcfo
nginx -t && systemctl reload nginx

# 6. Get SSL certificate (answer the prompts)
certbot --nginx -d ghostcfo.numbers10.co.za

# 7. Start the stack
docker compose up -d

# 8. Run database migrations
docker compose exec api alembic upgrade head

# 9. Seed the admin user
docker compose exec api python seed.py

# 10. Verify
curl https://ghostcfo.numbers10.co.za/api/health
```

---

## GitHub Actions secrets (set in repo Settings → Secrets)

| Secret | Value |
|--------|-------|
| `VPS_HOST` | Your Hetzner server IP |
| `VPS_USER` | `root` or deploy user |
| `VPS_SSH_KEY` | Private SSH key (no passphrase) |

After setting secrets, push to `main` to trigger automatic deploys.

---

## Adding a pilot client

```bash
# 1. Log into the portal as admin@numbers10.co.za
# 2. Go to Admin → Companies → create the company
# 3. Create a user (owner/bookkeeper) for the company
# 4. If Evolution client: Admin → Evolution Agents → provision agent
#    Copy the install command and run it on their server
# 5. If Partner client: give the bookkeeper their login credentials
#    and ask them to upload their first month's exports
```

---

## Running the pipeline locally (no Docker needed)

```bash
cd backend
pip install -r requirements.txt
python test_pipeline.py --input ../sample_data --output /tmp/ghostcfo_out
```

---

## Key log locations

```bash
docker compose logs api          # FastAPI logs
docker compose logs worker       # Celery task logs
docker compose logs beat         # Celery beat scheduler logs
C:\GhostCFO\agent.log            # Agent logs (on client's Windows server)
```
