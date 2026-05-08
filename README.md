# Ghost CFO

**AI-powered monthly financial reporting for South African SMBs running Sage Pastel.**

> Built and operated by [Numbers10 Technology Solutions](https://numbers10.co.za)

Ghost CFO connects to your Sage Pastel accounting system, reads your financial data, and delivers a plain-language report every month — like having a professional CFO on your team without the CFO price tag.

---

## What it does

Every month, Ghost CFO analyses your financials and sends you a report that says things like:

> *"October was a tough month for ABC Hardware. Revenue came in at R312,000 — 8% lower than September. Your payroll of R87,500 was your single biggest cost at 28% of revenue. You are currently owed R94,000 by customers — 3 invoices are overdue by more than 60 days and need urgent attention. At your current spending rate you have approximately 9 weeks of cash remaining. Recommended action: Call these 3 clients this week to collect payment before your next payroll run on the 25th."*

**Delivered as a PDF + WhatsApp message to the business owner. Every month. Automatically.**

---

## Pricing

| Plan | Price | Highlights |
|---|---|---|
| **Starter** | R500/month | Monthly PDF report, email delivery, 12-month history |
| **Professional** | R900/month | Everything + WhatsApp delivery + weekly cash pulse |
| **Premium** | R1,500/month | Everything + quarterly trends + anomaly alerts + custom commentary |

---

## Sage Pastel Integration

Ghost CFO supports the full Pastel product family:

- **Pastel Evolution** — Direct SQL connection via the Ghost CFO Agent (installed once on the client's server). Fully automatic.
- **Pastel Partner / Xpress** — Bookkeeper uploads 3–4 standard Pastel export files to the portal each month (5 minutes of work).
- **Pastel Payroll** — Payroll exports give a complete picture of true staff costs: gross pay, employer UIF + SDL, headcount changes, leave liability, and next-run warnings.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11 + FastAPI |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 + Alembic |
| Task queue | Celery + Redis |
| LLM narrative | DeepSeek V3 via OpenRouter |
| PDF generation | WeasyPrint |
| WhatsApp | Meta WhatsApp Business Cloud API |
| Email | SendGrid |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Agent (Windows) | Python → PyInstaller .exe + Windows Task Scheduler |
| Infrastructure | Docker + Nginx + Let's Encrypt on Hetzner Ubuntu 24 |
| CI/CD | GitHub Actions → GHCR → SSH deploy |

---

## Repository layout

```
backend/        FastAPI application
  app/
    api/          HTTP route handlers
    core/         Config, database, security, Celery
    models/       SQLAlchemy ORM models
    parsers/      Pastel Evolution SQL + Partner CSV/Excel parsers
    metrics/      Financial metrics engine
    narrative/    LLM prompt builder + OpenRouter client
    reports/      WeasyPrint PDF generator + templates
    tasks/        Celery background tasks (report generation, alerts, pulse)
  alembic/        Database migrations

frontend/       React portal + public marketing website
  src/
    pages/        Website.tsx (public), Login, Dashboard, Upload, Reports, Settings, Admin
    components/   ReportCard, TrendChart, HealthScoreRing, DebtorTable, etc.
    lib/          API client, auth helpers, TypeScript types

agent/          Ghost CFO Agent — Windows .exe for Evolution clients
  connector/      MS SQL Server connection + Evolution SQL queries
  sync/           Data extraction, AES-256 encryption, HTTPS upload
  service/        Windows Task Scheduler installer

nginx/          Nginx reverse proxy config (SSL, rate limiting, gzip)
sample_data/    Realistic SA test exports for local pipeline testing
```

---

## Quick start — local pipeline test (no Docker needed)

```bash
# 1. Configure environment
cp .env.example .env
# Fill in OPENROUTER_API_KEY (everything else works with defaults for local testing)

# 2. Install dependencies and run the pipeline
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python test_pipeline.py --input ../sample_data --output ../sample_data/output

# 3. Open the generated PDF
# sample_data/output/abc_hardware_2025-10.pdf
```

> **No API key?** The pipeline runs end-to-end using a deterministic stub narrator when `OPENROUTER_API_KEY` is not set — useful for testing parsers, metrics, and PDF layout offline.

---

## Run the full stack with Docker

```bash
cp .env.example .env        # fill in secrets
docker compose up --build

# Services:
#   API + docs    http://localhost:8000  (http://localhost:8000/docs)
#   Frontend      http://localhost:3000
#   PostgreSQL    localhost:5432  (user: ghostcfo / pass: ghostcfo)
#   Redis         localhost:6379
```

First-time database setup:
```bash
docker compose exec api alembic upgrade head
docker compose exec api python seed.py
```

---

## Production deployment

See [`DEPLOY.md`](DEPLOY.md) for the full VPS setup guide (Hetzner + Ubuntu 24 + Nginx + Certbot + Docker).

Production URL: `https://ghostcfo.numbers10.co.za`

---

## CI/CD

Push to `main` triggers GitHub Actions:
1. `ruff` lint + TypeScript type check + Vite build
2. Smoke test: runs the pipeline against sample data
3. Builds Docker images → pushes to GitHub Container Registry
4. SSHs to the Hetzner VPS → `docker compose pull` → restart → `alembic upgrade head`

GitHub Actions secrets required: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`

---

## Ghost CFO Agent (Pastel Evolution)

The agent is a Windows `.exe` installed once on the client's server by a Numbers10 technician:

```
GhostCFOAgent.exe --install --api-key=<key> --server=<sql-server> --db=<evolution-db>
```

It then runs automatically on the 1st of every month, extracts financial data from the Evolution SQL Server (read-only), encrypts the payload with AES-256-GCM, and POSTs it to the Ghost CFO API. No manual intervention needed after installation.

---

## Environment variables

All required variables are documented in [`.env.example`](.env.example).

---

## License

Proprietary software — © 2025–2026 Numbers10 Technology Solutions (Pty) Ltd.  
All rights reserved. Unauthorised copying, distribution, or use is prohibited.
