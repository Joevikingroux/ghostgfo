# GHOST CFO

## AI-Powered Financial Narrative Engine for South African SMBs

### Product by Numbers10 Technology Solutions — numbers10.co.za

### Built for Sage Pastel Evolution (SQL) + Sage Pastel Partner (Export) + Sage Pastel Payroll

-----

## WHAT IS GHOST CFO? (Read this first)

Ghost CFO is a monthly financial reporting service for small business owners in
South Africa. It connects to their Sage Pastel accounting system, reads their
financial data, and produces a clear, plain-language report — like having a
professional CFO on your team without paying CFO prices.

**The business owner receives a PDF and WhatsApp message every month that says:**

> “October was a tough month for ABC Hardware. Your revenue came in at R312,000
> which is 8% lower than September. Your payroll this month was R87,500 covering
> 12 employees — your single biggest cost at 28% of revenue. Staff costs increased
> by R18,000 versus last month due to 2 overtime-heavy weeks. You are currently
> owed R94,000 by customers — 3 invoices are overdue by more than 60 days and need
> urgent attention. At your current spending rate, you have approximately 9 weeks
> of cash remaining. Recommended action: Call these 3 clients this week to collect
> payment before your next payroll run on the 25th.”

That is Ghost CFO. Simple. Valuable. Nobody else is doing this for South African SMBs.

-----

## WHO IS THIS FOR?

- Small business owners who use Sage Pastel but don’t fully understand their numbers
- Companies that have a bookkeeper but no financial manager or CFO
- Any SA business with monthly revenue between R100k and R5 million
- Numbers10 existing Pastel clients (first customers — warm leads already exist)

-----

## THE THREE DATA SOURCE MODES

Ghost CFO supports three ways to get financial data, covering the full Sage
Pastel product family. Most clients will use a combination of these:

### MODE 1 — PASTEL EVOLUTION (Direct SQL Connection)

Sage Pastel Evolution stores all data in a Microsoft SQL Server database.
Ghost CFO connects directly to that database (read-only) using a secure
SQL Server connection. The system pulls live financial data automatically —
no manual exports needed after initial setup.

**Best for:** Medium businesses, multi-user Pastel Evolution installations

**How it works:**

1. Numbers10 installs a small Ghost CFO Agent on the client’s server
1. Agent connects to the Pastel Evolution SQL Server (read-only credentials)
1. Agent sends encrypted financial snapshots to Ghost CFO cloud every month
1. Report is generated and delivered automatically

### MODE 2 — PASTEL PARTNER (File Upload)

Sage Pastel Partner does not have a direct SQL connection available.
The bookkeeper exports standard reports from Pastel and uploads them to the
Ghost CFO portal once a month. The system reads these files automatically.

**Supported export formats:**

- Income Statement (CSV or Excel .xls/.xlsx)
- Balance Sheet (CSV or Excel)
- Debtor Age Analysis (CSV or Excel)
- Creditor Age Analysis (CSV or Excel — optional)

**Best for:** Smaller businesses on Pastel Partner/Xpress

**How it works:**

1. Bookkeeper logs into Ghost CFO portal
1. Uploads 3–4 standard Pastel export files (takes 5 minutes)
1. System reads the files and generates the report automatically
1. Business owner receives their report

### MODE 3 — SAGE PASTEL PAYROLL (File Export)

Sage Pastel Payroll is a separate product from the accounting system. It manages
employee salaries, PAYE, UIF, SDL, leave, and all statutory payroll submissions.
Ghost CFO reads Payroll exports to give the business owner a complete picture of
their staff costs — typically their single largest expense.

**Why payroll data matters for the report:**
Most SA SMBs have no idea what their real staff cost is. The salary on the payslip
is not the full story. Ghost CFO calculates the TRUE employer cost: gross salary +
employer UIF + SDL + any employer medical aid contributions. It then shows payroll
as a percentage of revenue, flags if the wage bill is growing faster than income,
and warns if the next payroll run cannot be covered by available cash.

**Supported export formats from Sage Pastel Payroll:**

- Payroll Summary Report (CSV or Excel) — total gross, deductions, net pay per period
- Employee Cost Report (CSV or Excel) — full employer cost including UIF, SDL contributions
- Leave Liability Report (CSV or Excel) — outstanding leave balance as a rand liability
- Payslip Journal Export (CSV) — GL postings for reconciliation with accounting system

**Best for:** All clients who use Sage Pastel Payroll (standalone or linked to Evolution/Partner)

**How it works:**

1. Payroll administrator exports the above reports from Pastel Payroll at month-end
1. Uploads them to the Ghost CFO portal alongside the accounting exports
1. Ghost CFO combines payroll + accounting data into one unified report
1. Business owner sees staff costs, headcount, leave liability, and payroll warnings

**What Ghost CFO extracts from Payroll exports:**

|Data Point                   |Plain English Meaning                                    |
|-----------------------------|---------------------------------------------------------|
|Total gross payroll          |What all employees earned before any deductions          |
|Total net payroll            |What actually left the bank account to employees         |
|Employer UIF contribution    |Your share of UIF (1% of gross, paid to SARS)            |
|SDL levy                     |Skills Development Levy (1% of gross, paid to SARS)      |
|Total true employer cost     |Gross + all employer contributions = real staff cost     |
|Headcount                    |Number of employees on the payroll this month            |
|Payroll % of revenue         |Staff cost as a share of income (key efficiency metric)  |
|Month-on-month payroll change|Did the wage bill go up? By how much? Why?               |
|Outstanding leave liability  |Rand value owed to staff if they all resigned today      |
|Next payroll run date        |Used to warn if cash runway is shorter than payroll cycle|

**Double-counting prevention (important):**
Pastel Payroll can post a payroll journal directly into Pastel Evolution or Partner GL.
If this journal posting is active, salary costs already appear in the accounting GL.
In this case Ghost CFO:

- Uses the GL salary figures for the revenue/cost calculations (avoids double-counting)
- Uses the Payroll export ONLY for the detailed breakdown (headcount, leave liability, UIF/SDL split)
- Flags in the report whether payroll journal integration is detected or not
  The parser must auto-detect this by checking if a payroll-linked GL account exists in the chart of accounts.

**Payroll-specific alerts Ghost CFO will send:**

- Payroll grew more than 10% vs last month (flag for review)
- Payroll exceeds 40% of revenue (sustainability warning)
- Leave liability exceeds 4 weeks of payroll (cash risk warning)
- Cash balance less than 1.5x next payroll run (urgent cash warning)
- Number of employees changed (hired or resigned — notable for owner)

-----

## VISION & BUSINESS PLAN

### The Problem (In Plain English)

Most small business owners in South Africa:

- Have a bookkeeper who captures invoices and payments (looking backwards)
- Receive a trial balance or financial statements they don’t understand
- Have no one to explain what the numbers actually mean
- Only find out something is wrong when the bank calls or cash runs out

A real CFO costs R50,000–R150,000/month. Ghost CFO delivers the same insight
for R500–R1,500/month using AI.

### Revenue Model

```
STARTER PLAN       — R500/month
  ✓ Monthly PDF report (plain language)
  ✓ Email delivery
  ✓ 12-month report history
  ✓ Pastel Partner file upload OR Evolution SQL

PROFESSIONAL PLAN  — R900/month
  ✓ Everything in Starter
  ✓ WhatsApp delivery to business owner
  ✓ Weekly cash pulse (1-paragraph WhatsApp update)
  ✓ Debtor alert notifications (when invoices go overdue)

PREMIUM PLAN       — R1,500/month
  ✓ Everything in Professional
  ✓ Quarterly trend analysis and year-on-year comparison
  ✓ Anomaly alerts (unusual cost spikes, revenue drops)
  ✓ Custom commentary section (Numbers10 adds manual notes)
  ✓ Priority support
```

### 6-Month Growth Target

```
Month 1  →  Building the product (R0 revenue)
Month 2  →  3 free pilot clients from existing Numbers10 base
Month 3  →  3 paying clients @ R600 avg = R1,800/month
Month 4  →  8 paying clients @ R600 avg = R4,800/month
Month 5  →  15 paying clients @ R700 avg = R10,500/month
Month 6  →  25 paying clients @ R700 avg = R17,500/month
```

**Goal: R15,000–R20,000 recurring monthly income by Month 6.**
This requires 25 clients. Numbers10 already has relationships with enough
Pastel clients to reach this target without any cold outreach.

-----

## FULL TECHNICAL ARCHITECTURE

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                                │
│                                                                 │
│  ┌──────────────────┐  ┌─────────────────────┐  ┌──────────────┐  │
│  │ PASTEL EVOLUTION │  │   PASTEL PARTNER    │  │  PASTEL      │  │
│  │ SQL Server DB    │  │   File Uploads      │  │  PAYROLL     │  │
│  │ (direct,        │  │   (CSV/Excel)       │  │  File Export │  │
│  │  read-only)     │  │                     │  │  (CSV/Excel) │  │
│  └───────┬──────────┘  └──────────┬──────────┘  └──────┬───────┘  │
│          │                        │                     │          │
│   Ghost CFO Agent           Upload Portal          Upload Portal   │
│   (on client server)        (bookkeeper)           (payroll admin) │
└──────────┼────────────────────────┼─────────────────────┼──────────┘
           │                        │                     │
           └────────────────┬───────┴─────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GHOST CFO BACKEND (FastAPI)                   │
│                                                                 │
│   Parser & Normaliser  →  Metrics Engine  →  LLM Narrative     │
│                                ↓                               │
│              PDF Generator + WhatsApp Sender                   │
└─────────────────────────────────────────────────────────────────┘
            │                                │
            ▼                                ▼
     Client Dashboard                  Business Owner
     (web portal)                   PDF + WhatsApp report
```

-----

## TECH STACK

### Backend

- **Language:** Python 3.11+
- **Framework:** FastAPI (async, fast, clean API design)
- **Database:** PostgreSQL (Ghost CFO’s own data — clients, reports, users)
- **ORM:** SQLAlchemy 2.0 + Alembic (database migrations)
- **Task Queue:** Celery + Redis (generate reports in background, don’t block UI)
- **PDF Generation:** WeasyPrint (renders HTML/CSS templates to PDF)
- **LLM:** DeepSeek V3 via OpenRouter API (cost-effective, excellent at financial text)
- **WhatsApp:** Meta WhatsApp Business Cloud API
- **Email:** SendGrid or SMTP (transactional emails)
- **Pastel Evolution SQL:** pyodbc + FreeTDS (connects to MS SQL Server)
- **File Parsing:** pandas + openpyxl (reads Pastel Partner CSV/Excel exports)
- **Payroll Parsing:** pandas (reads Pastel Payroll CSV/Excel exports — separate parser module)

### Frontend

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **Charts:** Recharts (revenue trends, cost breakdowns, cash runway)
- **Auth:** JWT tokens in httpOnly cookies
- **Forms:** React Hook Form + Zod validation

### Brand & Design (Numbers10 Standard)

- **Background:** Pure black (#000000)
- **Primary Accent:** Teal-to-cyan gradient (#2DD4BF → #06B6D4)
- **Heading Font:** Space Grotesk
- **Body Font:** Inter
- **Code Font:** JetBrains Mono
- **Report PDF styling:** Clean white, professional, readable by non-technical users

### Infrastructure

- **Server:** Ubuntu 24 LTS VPS (Hetzner — existing Numbers10 relationship)
- **Containers:** Docker + Docker Compose
- **Reverse Proxy:** Nginx
- **SSL:** Let’s Encrypt / Certbot
- **Domain:** ghostcfo.co.za (primary) or ghostcfo.numbers10.co.za (staging)
- **Backups:** PostgreSQL daily dumps → Synology NAS → Hetzner Storage Box
- **CI/CD:** GitHub Actions → SSH deploy to VPS
- **Repo:** github.com/Joevikingroux/ghostcfo

### Ghost CFO Agent (for Evolution clients)

- **Language:** Python (compiled to .exe with PyInstaller for Windows deployment)
- **Runs as:** Windows Service (NSSM wrapper)
- **Schedule:** 1st of every month, 06:00 AM (configurable)
- **Connection:** Read-only pyodbc connection to local Pastel Evolution SQL Server
- **Security:** AES-256 encrypted payload, HTTPS only, API key auth
- **Signing:** Numbers10 code-signed executable (professional deployment)

-----

## PROJECT FILE STRUCTURE

```
ghostcfo/
│
├── CLAUDE.md                          ← You are here
├── README.md
├── docker-compose.yml                 ← Spins up all services
├── docker-compose.dev.yml             ← Local dev overrides
├── .env.example                       ← All required env vars documented
├── .gitignore
│
├── backend/                           ← FastAPI application
│   ├── main.py                        ← App entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── app/
│   │   ├── api/                       ← All HTTP routes
│   │   │   ├── auth.py                ← Login, register, JWT
│   │   │   ├── companies.py           ← Manage client companies
│   │   │   ├── uploads.py             ← Partner file upload endpoints
│   │   │   ├── reports.py             ← Report retrieval + download
│   │   │   ├── agent.py               ← Evolution agent data ingestion
│   │   │   └── webhooks.py            ← WhatsApp webhook receiver
│   │   │
│   │   ├── core/
│   │   │   ├── config.py              ← Settings from .env
│   │   │   ├── database.py            ← PostgreSQL connection
│   │   │   ├── security.py            ← JWT + password hashing
│   │   │   └── celery_app.py          ← Celery + Redis setup
│   │   │
│   │   ├── models/                    ← SQLAlchemy ORM models
│   │   │   ├── company.py
│   │   │   ├── user.py
│   │   │   ├── upload.py
│   │   │   └── report.py
│   │   │
│   │   ├── parsers/                   ← Data ingestion layer
│   │   │   ├── base.py                ← Abstract base parser
│   │   │   ├── evolution_sql.py       ← Pastel Evolution SQL Server queries
│   │   │   ├── partner_income.py      ← Partner Income Statement parser
│   │   │   ├── partner_balance.py     ← Partner Balance Sheet parser
│   │   │   ├── partner_debtors.py     ← Partner Debtor Age Analysis parser
│   │   │   └── partner_creditors.py   ← Partner Creditor Age Analysis parser
│   │   │
│   │   ├── metrics/                   ← Financial calculations
│   │   │   ├── engine.py              ← Main metrics orchestrator
│   │   │   ├── revenue.py             ← Revenue trend, growth, seasonality
│   │   │   ├── costs.py               ← Cost analysis, movers, ratios
│   │   │   ├── debtors.py             ← Debtor days, overdue flags, aging
│   │   │   ├── creditors.py           ← Creditor days, payment health
│   │   │   ├── cash.py                ← Cash position, burn rate, runway
│   │   │   └── ratios.py              ← Gross margin, net margin, liquidity
│   │   │
│   │   ├── narrative/                 ← LLM narrative generation
│   │   │   ├── generator.py           ← Main LLM orchestrator
│   │   │   ├── prompts.py             ← All LLM prompt templates
│   │   │   ├── tone.py                ← Language/tone settings (EN/AF)
│   │   │   └── openrouter.py          ← OpenRouter API client
│   │   │
│   │   ├── reports/                   ← Output generation
│   │   │   ├── pdf_generator.py       ← WeasyPrint PDF builder
│   │   │   ├── templates/             ← HTML/CSS report templates
│   │   │   │   ├── monthly_report.html
│   │   │   │   ├── weekly_pulse.html
│   │   │   │   └── styles.css
│   │   │   └── whatsapp.py            ← WhatsApp message formatter + sender
│   │   │
│   │   └── tasks/                     ← Celery background tasks
│   │       ├── generate_report.py     ← Full monthly report pipeline
│   │       ├── weekly_pulse.py        ← Weekly cash pulse task
│   │       └── debtor_alerts.py       ← Overdue invoice notifications
│   │
│   └── alembic/                       ← Database migrations
│       ├── env.py
│       └── versions/
│
├── frontend/                          ← React dashboard
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       │
│       ├── pages/
│       │   ├── Login.tsx              ← Login page
│       │   ├── Dashboard.tsx          ← Overview for business owner
│       │   ├── Reports.tsx            ← Report history + downloads
│       │   ├── Upload.tsx             ← Partner file upload page
│       │   ├── Settings.tsx           ← Company settings, WhatsApp number
│       │   └── Admin.tsx              ← Numbers10 admin — all clients
│       │
│       ├── components/
│       │   ├── ReportCard.tsx         ← Single report summary card
│       │   ├── MetricTile.tsx         ← Revenue / cash / debtor tiles
│       │   ├── TrendChart.tsx         ← Revenue trend line chart
│       │   ├── DebtorTable.tsx        ← Overdue invoice table
│       │   ├── UploadDropzone.tsx     ← Drag-and-drop file uploader
│       │   └── StatusBadge.tsx        ← Report status indicator
│       │
│       └── lib/
│           ├── api.ts                 ← Axios API client
│           ├── auth.ts                ← Auth helpers
│           └── types.ts               ← TypeScript interfaces
│
└── agent/                             ← Ghost CFO Agent (Windows .exe)
    ├── main.py                        ← Agent entry point
    ├── requirements.txt
    ├── build.spec                     ← PyInstaller build config
    │
    ├── connector/
    │   ├── evolution_db.py            ← MS SQL Server connection + queries
    │   └── queries.py                 ← All Pastel Evolution SQL queries
    │
    ├── sync/
    │   ├── extractor.py               ← Pulls and structures financial data
    │   ├── encryptor.py               ← AES-256 payload encryption
    │   └── uploader.py                ← HTTPS POST to Ghost CFO API
    │
    └── service/
        ├── installer.py               ← Windows service installer (NSSM)
        └── scheduler.py               ← Monthly run scheduler
```

-----

## DATABASE SCHEMA (PostgreSQL — Ghost CFO’s own database)

```sql
-- Every SMB client is a company record
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    trading_name    TEXT,
    reg_number      TEXT,
    vat_number      TEXT,
    industry        TEXT,
    -- Contact details
    owner_name      TEXT,
    owner_email     TEXT,
    owner_whatsapp  TEXT,          -- Format: +27821234567
    bookkeeper_name TEXT,
    bookkeeper_email TEXT,
    -- Plan and billing
    plan            TEXT DEFAULT 'starter',  -- starter|professional|premium
    plan_start_date DATE,
    active          BOOLEAN DEFAULT true,
    -- Data source
    data_source     TEXT DEFAULT 'partner',  -- partner|evolution
    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Evolution clients get an agent config record
CREATE TABLE evolution_agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    api_key         TEXT UNIQUE NOT NULL,   -- Agent authenticates with this
    server_name     TEXT,                   -- Client's server hostname
    db_name         TEXT,                   -- Evolution database name
    last_sync_at    TIMESTAMPTZ,
    last_sync_status TEXT,
    active          BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- All users — business owners and bookkeepers
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    full_name       TEXT,
    role            TEXT DEFAULT 'viewer',  -- owner|bookkeeper|admin
    active          BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- File uploads (Partner mode only)
CREATE TABLE uploads (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id            UUID REFERENCES companies(id) ON DELETE CASCADE,
    uploaded_by           UUID REFERENCES users(id),
    period_month          INT NOT NULL,   -- 1–12
    period_year           INT NOT NULL,   -- e.g. 2025
    -- File paths for each upload type
    income_statement_path TEXT,
    balance_sheet_path    TEXT,
    debtors_age_path      TEXT,
    creditors_age_path    TEXT,
    -- Payroll export file paths (optional but recommended)
    payroll_summary_path       TEXT,
    payroll_employee_cost_path TEXT,
    payroll_leave_path         TEXT,
    payroll_journal_path       TEXT,
    payroll_journal_integrated BOOLEAN DEFAULT false,  -- TRUE if payroll posts to GL
    -- Processing status
    status  TEXT DEFAULT 'pending',  -- pending|processing|complete|failed
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generated reports (one per company per month)
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    upload_id       UUID REFERENCES uploads(id),       -- NULL for Evolution
    period_month    INT NOT NULL,
    period_year     INT NOT NULL,
    -- Raw computed metrics (stored as JSON for flexibility)
    metrics         JSONB NOT NULL DEFAULT '{}',
    -- LLM-generated narrative sections
    narrative_summary    TEXT,     -- 2–3 sentence executive summary
    narrative_revenue    TEXT,     -- Revenue section
    narrative_costs      TEXT,     -- Cost section
    narrative_debtors    TEXT,     -- Debtors section
    narrative_cash       TEXT,     -- Cash position section
    narrative_actions    TEXT,     -- Recommended actions (most important)
    -- Output files
    pdf_path        TEXT,
    -- Delivery status
    email_sent      BOOLEAN DEFAULT false,
    email_sent_at   TIMESTAMPTZ,
    whatsapp_sent   BOOLEAN DEFAULT false,
    whatsapp_sent_at TIMESTAMPTZ,
    -- Metadata
    generated_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, period_month, period_year)
);
```

-----

## PASTEL EVOLUTION SQL QUERIES

These queries run against the client’s Pastel Evolution MS SQL Server database.
All connections are READ-ONLY. Ghost CFO never writes to the client’s database.

### Key Evolution Tables to Query

```
_btblGLTransactions      ← General Ledger transactions (revenue, costs)
_btblGLAccounts          ← Chart of accounts (account names and types)
_btblGLPeriods           ← Financial periods
_btblARTransactions      ← Accounts Receivable (debtors / customers)
_btblARCustomers         ← Customer master data
_btblAPTransactions      ← Accounts Payable (creditors / suppliers)
_btblAPSuppliers         ← Supplier master data
_btblCashBookTransactions ← Cash book entries
```

### Revenue Query (Monthly)

```sql
SELECT
    p.cPeriodName AS period,
    p.dPeriodDate AS period_date,
    SUM(CASE WHEN a.iAccountType = 4 THEN t.dDebit - t.dCredit ELSE 0 END)
        AS total_revenue
FROM _btblGLTransactions t
JOIN _btblGLAccounts a ON t.iAccountID = a.iAccountID
JOIN _btblGLPeriods p ON t.iPeriodID = p.iPeriodID
WHERE a.iAccountType = 4  -- Income accounts
  AND p.dPeriodDate >= DATEADD(month, -12, GETDATE())
GROUP BY p.cPeriodName, p.dPeriodDate
ORDER BY p.dPeriodDate;
```

### Debtor Age Analysis Query

```sql
SELECT
    c.cCustomerCode,
    c.cCustomerName,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, GETDATE()) <= 30
        THEN t.dBalance ELSE 0 END) AS current_amount,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, GETDATE()) BETWEEN 31 AND 60
        THEN t.dBalance ELSE 0 END) AS days_30_60,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, GETDATE()) BETWEEN 61 AND 90
        THEN t.dBalance ELSE 0 END) AS days_61_90,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, GETDATE()) > 90
        THEN t.dBalance ELSE 0 END) AS over_90_days,
    SUM(t.dBalance) AS total_outstanding
FROM _btblARTransactions t
JOIN _btblARCustomers c ON t.iCustomerID = c.iCustomerID
WHERE t.dBalance > 0
  AND t.iTransactionType IN (1, 2)  -- Invoices and credit notes
GROUP BY c.cCustomerCode, c.cCustomerName
HAVING SUM(t.dBalance) > 0
ORDER BY over_90_days DESC;
```

-----

## SAGE PASTEL PAYROLL SQL QUERIES

Pastel Payroll uses its own SQL Server database (separate from Evolution).
When the agent detects a linked Payroll database, it queries it directly.
For standalone Payroll (not linked to Evolution), use the file export path.

### Key Payroll Tables

```
PayrollMaster          ← Employee master records
PayrollTransaction     ← All payroll transactions per employee per period
PayrollComponent       ← Pay components (basic, overtime, bonus, deduction types)
PayrollPeriod          ← Pay periods (monthly, weekly, fortnightly)
LeaveTransaction       ← Leave taken and balances per employee
LeaveType              ← Leave type definitions (annual, sick, family)
StatutoryReturns       ← EMP201 / IRP5 statutory totals
```

### Monthly Payroll Summary Query

```sql
SELECT
    pp.PeriodDescription,
    pp.PeriodEndDate,
    COUNT(DISTINCT pt.EmployeeID)        AS headcount,
    SUM(CASE WHEN pc.ComponentType = 'Earnings'
        THEN pt.Amount ELSE 0 END)       AS gross_payroll,
    SUM(CASE WHEN pc.ComponentCode = 'UIF_EE'
        THEN pt.Amount ELSE 0 END)       AS employee_uif,
    SUM(CASE WHEN pc.ComponentCode = 'UIF_ER'
        THEN pt.Amount ELSE 0 END)       AS employer_uif,
    SUM(CASE WHEN pc.ComponentCode = 'SDL'
        THEN pt.Amount ELSE 0 END)       AS employer_sdl,
    SUM(CASE WHEN pc.ComponentCode = 'PAYE'
        THEN pt.Amount ELSE 0 END)       AS paye_deducted,
    SUM(CASE WHEN pc.ComponentType = 'Earnings'
        THEN pt.Amount ELSE 0 END)
    - SUM(CASE WHEN pc.ComponentType = 'Deductions'
        THEN pt.Amount ELSE 0 END)       AS net_payroll
FROM PayrollTransaction pt
JOIN PayrollComponent pc   ON pt.ComponentID = pc.ComponentID
JOIN PayrollPeriod pp      ON pt.PeriodID = pp.PeriodID
WHERE pp.PeriodEndDate >= DATEADD(month, -12, GETDATE())
GROUP BY pp.PeriodDescription, pp.PeriodEndDate
ORDER BY pp.PeriodEndDate;
```

### Leave Liability Query (what the business owes staff in rand)

```sql
SELECT
    pm.EmployeeName,
    lt.LeaveTypeName,
    lb.BalanceDays,
    pm.BasicSalary / 21.67             AS daily_rate,  -- 21.67 = avg working days/month
    (lb.BalanceDays * pm.BasicSalary / 21.67) AS liability_rand
FROM LeaveBalance lb
JOIN PayrollMaster pm  ON lb.EmployeeID = pm.EmployeeID
JOIN LeaveType lt      ON lb.LeaveTypeID = lt.LeaveTypeID
WHERE lt.LeaveTypeName = 'Annual Leave'
  AND lb.BalanceDays > 0
ORDER BY liability_rand DESC;
```

### Payroll GL Journal Detection Query

```sql
-- Check if payroll is configured to post to Evolution GL
-- If this returns rows, payroll costs are already in the accounting GL
SELECT
    js.JournalDate,
    js.GLAccountCode,
    js.Amount,
    js.Description
FROM PayrollGLJournal js
WHERE js.JournalDate >= DATEADD(month, -1, GETDATE())
  AND js.Posted = 1
ORDER BY js.JournalDate DESC;
```

-----

## PASTEL PARTNER FILE FORMATS

### Expected Income Statement CSV columns

```
Account Code | Account Description | Current Month | Previous Month | YTD | Budget
```

### Expected Balance Sheet CSV columns

```
Account Code | Account Description | Current Balance | Previous Balance
```

### Expected Debtor Age Analysis CSV columns

```
Customer Code | Customer Name | Current | 30 Days | 60 Days | 90 Days | 90+ Days | Total
```

### Expected Payroll Summary CSV columns

```
Employee Code | Employee Name | Department | Gross Pay | PAYE | UIF (EE) | UIF (ER) | SDL | Other Deductions | Net Pay
```

### Expected Employee Cost Report CSV columns

```
Employee Code | Employee Name | Basic Salary | Overtime | Bonus | Total Gross | Employer UIF | Employer SDL | Total Employer Cost
```

### Expected Leave Liability Report CSV columns

```
Employee Code | Employee Name | Leave Type | Balance Days | Daily Rate | Liability (Rand)
```

**Payroll parser edge cases to handle:**

- Summary/total rows at the bottom (exclude from per-employee calculations)
- Terminated employees included in month (flag headcount change)
- Negative amounts for salary deductions (e.g. loan repayments)
- Multiple pay frequencies in one export (monthly + weekly staff mixed)
- Department subtotals (skip these rows, only use employee-level detail)
- YTD columns mixed with current-period columns (use current period only)

The parser must handle:

- Different column name spellings across Pastel versions
- Blank rows used as section separators
- Summary/subtotal rows (must be excluded from detail calculations)
- Negative values for credit entries
- Comma-formatted numbers (e.g. “1,234,567.00”)
- Values in parentheses as negatives (e.g. “(45,000.00)”)

-----

## METRICS ENGINE — WHAT WE CALCULATE

Every report computes these metrics and stores them in the `metrics` JSONB column:

```python
{
  # Revenue
  "revenue_current_month": 312000.00,
  "revenue_previous_month": 339130.00,
  "revenue_change_pct": -7.99,
  "revenue_ytd": 2845000.00,
  "revenue_trend": "declining",          # growing|stable|declining

  # Gross Profit
  "gross_profit_current": 187200.00,
  "gross_margin_pct": 60.0,
  "gross_margin_prev_pct": 61.2,
  "gross_margin_trend": "stable",

  # Costs
  "total_costs_current": 124800.00,
  "total_costs_previous": 108000.00,
  "cost_change_pct": 15.56,
  "top_cost_mover": "Salaries",
  "top_cost_mover_change": 18000.00,
  "top_cost_mover_change_pct": 22.5,

  # Debtors
  "debtors_total": 94000.00,
  "debtors_current": 45000.00,
  "debtors_30_60_days": 28000.00,
  "debtors_61_90_days": 12000.00,
  "debtors_over_90_days": 9000.00,
  "debtor_days": 54.2,                  # Average collection days
  "overdue_invoices_count": 3,
  "overdue_invoices_value": 21000.00,
  "debtors_health": "warning",          # good|warning|critical

  # Cash
  "cash_balance": 87000.00,
  "monthly_burn_rate": 124800.00,
  "cash_runway_weeks": 9.1,
  "cash_health": "warning",             # good|warning|critical

  # Payroll
  "payroll_gross_total": 87500.00,
  "payroll_net_total": 71200.00,
  "payroll_employer_uif": 875.00,
  "payroll_employer_sdl": 875.00,
  "payroll_true_employer_cost": 89250.00,
  "payroll_headcount": 12,
  "payroll_headcount_change": 0,           # +/- vs last month
  "payroll_pct_of_revenue": 28.6,
  "payroll_pct_prev_month": 24.1,
  "payroll_change_pct": 18.5,
  "leave_liability_rand": 34200.00,
  "leave_liability_weeks_payroll": 1.8,
  "next_payroll_date": "2025-11-25",
  "cash_covers_payroll": true,             # false = urgent alert
  "payroll_health": "warning",             # good|warning|critical

  # Overall Health Score (0–100)
  "health_score": 61,
  "health_rating": "fair",              # excellent|good|fair|poor|critical
  "health_flags": [
    "Revenue declining 3 consecutive months",
    "3 invoices overdue 60+ days",
    "Cash runway below 12 weeks"
  ]
}
```

-----

## LLM NARRATIVE — HOW IT WORKS

The metrics JSON is passed to DeepSeek V3 via OpenRouter with a structured prompt.
The model generates plain-language narrative sections in the business owner’s language.

### System Prompt

```
You are Ghost CFO, a friendly but professional financial advisor for South African
small businesses. You receive structured financial metrics and write clear,
plain-language reports that non-financial business owners can understand and act on.

Rules:
- Write in simple, direct English (or Afrikaans if specified)
- Never use accounting jargon without explaining it
- Always include specific rand amounts, not just percentages
- Always end with clear, numbered action items
- Be honest about problems — don't sugarcoat, but stay encouraging
- Keep each section to 3–5 sentences maximum
- Write as if you are talking directly to the business owner
```

### Report Sections Generated

1. **Executive Summary** — 2-3 sentences, overall picture
1. **Revenue** — What revenue did, why it matters
1. **Costs** — What costs did, what moved most
1. **Customers (Debtors)** — Who owes money, what’s overdue
1. **Payroll & Staff Costs** — What the wage bill was, headcount, leave liability, next run
1. **Cash Position** — How much cash, how long it lasts, whether next payroll is covered
1. **Action Items** — Numbered list, most urgent first

-----

## GHOST CFO AGENT (WINDOWS .EXE FOR EVOLUTION)

The agent runs on the client’s Windows server. It is installed once by Numbers10
and then runs automatically every month.

### What It Does

1. Connects to local Pastel Evolution SQL Server (read-only)
1. Runs the standard financial queries
1. If Pastel Payroll is linked to Evolution, also queries the Payroll database
1. Structures the data into a JSON payload
1. Encrypts the payload with AES-256
1. Sends it to the Ghost CFO API via HTTPS
1. Logs the result to a local log file

### Installation Steps (for Numbers10 technician)

```
1. Copy GhostCFOAgent.exe to C:\GhostCFO\
2. Run: GhostCFOAgent.exe --install --api-key=<company_api_key>
           --server=<sql_server_name> --db=<evolution_db_name>
3. Agent installs itself as a Windows Service (runs as SYSTEM)
4. First sync runs immediately to test connection
5. Confirm in Ghost CFO admin portal that data is received
```

### Security

- The agent uses a unique API key per client (generated in Ghost CFO admin)
- All data is encrypted before leaving the client’s server
- The SQL user used has SELECT-only permissions on Evolution tables
- No data is ever written to the client’s Evolution database
- Payload is sent via HTTPS only — no plain HTTP fallback

-----

## ENVIRONMENT VARIABLES (.env)

```bash
# Application
APP_NAME=GhostCFO
APP_ENV=production                        # development|staging|production
SECRET_KEY=<generate-with-openssl-rand-hex-32>
BASE_URL=https://ghostcfo.co.za

# PostgreSQL (Ghost CFO's own database)
DATABASE_URL=postgresql://ghostcfo:password@localhost:5432/ghostcfo

# Redis (task queue)
REDIS_URL=redis://localhost:6379/0

# OpenRouter (LLM)
OPENROUTER_API_KEY=<your-openrouter-key>
OPENROUTER_MODEL=deepseek/deepseek-chat  # DeepSeek V3

# WhatsApp Business Cloud API
WHATSAPP_PHONE_NUMBER_ID=<meta-phone-number-id>
WHATSAPP_ACCESS_TOKEN=<meta-access-token>
WHATSAPP_VERIFY_TOKEN=<your-webhook-verify-token>

# Email (SendGrid)
SENDGRID_API_KEY=<your-sendgrid-key>
FROM_EMAIL=reports@ghostcfo.co.za
FROM_NAME=Ghost CFO

# File Storage
UPLOAD_DIR=/app/uploads
REPORTS_DIR=/app/reports

# Agent Security
AGENT_ENCRYPTION_KEY=<generate-32-byte-key>  # AES-256 key for agent payloads

# Payroll
PAYROLL_DB_ENABLED=false          # Set true when client has linked Payroll SQL DB
PAYROLL_JOURNAL_GL_ACCOUNT=7100   # GL account code used for payroll journal postings
                                   # Used to detect double-counting risk
```

-----

## BUILD ORDER — WHAT TO BUILD FIRST

Follow this exact order. Do not skip phases.

### PHASE 1 — Foundation (Week 1)

**Goal: Get data in, get a report out. Nothing else.**

1. `docker-compose.yml` — PostgreSQL + Redis + FastAPI + Celery
1. Database schema + Alembic migrations
1. Pastel Partner CSV/Excel parsers (Income Statement + Balance Sheet + Debtors)
1. Pastel Payroll CSV parsers (Payroll Summary + Employee Cost + Leave Liability)
1. Metrics engine (revenue, costs, debtors, cash, payroll — basic versions)
1. LLM narrative generator (single prompt, plain text output)
1. WeasyPrint PDF generator (basic template, readable layout)
1. CLI test script: `python test_pipeline.py --input ./sample_data/`

**Success criteria:** Feed in Partner + Payroll sample CSV files → receive a PDF report that includes staff cost analysis.

### PHASE 2 — Web Portal (Week 2)

**Goal: Bookkeeper can upload files. Business owner can download report.**

1. FastAPI auth endpoints (login, JWT, refresh)
1. Company + user management endpoints
1. File upload endpoint (Partner mode)
1. Report generation triggered on upload (Celery task)
1. Report retrieval + PDF download endpoint
1. React frontend: Login → Upload page → Reports page

**Success criteria:** Full browser flow works end-to-end with 1 test company.

### PHASE 3 — Delivery (Week 3)

**Goal: Reports actually reach the business owner.**

1. Email delivery (SendGrid) — PDF attached, branded template
1. WhatsApp delivery (Meta API) — short narrative summary + PDF link
1. Delivery status tracking in database
1. Retry logic for failed deliveries

**Success criteria:** Business owner receives report on WhatsApp and email.

### PHASE 4 — Evolution Agent (Week 4)

**Goal: Automatic data pull from Pastel Evolution clients.**

1. Evolution SQL queries (revenue, costs, debtors, creditors, cash)
1. Payroll SQL queries (if Payroll DB is linked to Evolution) — headcount, gross, leave liability
1. Agent `main.py` with pyodbc connection
1. AES-256 payload encryption
1. Agent API endpoint on Ghost CFO backend (receives + stores payload)
1. PyInstaller build → signed Windows .exe
1. Windows service installer
1. Agent management page in admin portal

**Success criteria:** Agent installed on test Evolution server → data arrives → report generated automatically.

### PHASE 5 — Polish + First Clients (Week 5–6)  ✓ COMPLETE

1. Numbers10 admin dashboard (all companies, status, MRR overview)
1. Client dashboard improvements (trend charts, health score ring, debtor aging bar)
1. PDF template polish (cash runway bar, debtor aging bar, WeasyPrint CSS fix)
1. Afrikaans language option for reports (full Afrikaans prompts, per-company setting)
1. Debtor alert notifications (daily Celery beat, 61-day threshold)
1. Weekly cash pulse (Monday 07:00 SAST, Professional + Premium)
1. GitHub Actions CI/CD (lint + build + smoke test + deploy to Hetzner)
1. Production nginx config (SSL termination, rate limiting, loopback binding)

### PHASE 6 — Public Website (ghostcfo.numbers10.co.za)

**Goal: The domain is a marketing website first. Portal is accessed via "Client Login".**

1. Public landing page (`/`) — hero, features, pricing, how it works, about, CTA
2. Update routing in `App.tsx` — `/` → website, `/login` → portal login
3. Mobile-responsive navbar with hamburger menu
4. Pricing section with plan comparison table
5. Pastel compatibility badges
6. Footer with Numbers10 branding and legal links

-----

## SAMPLE DATA (Create These Files for Testing)

Create `sample_data/` folder with realistic test files:

- `income_statement_oct2025.csv` — 12 months of revenue + cost lines
- `balance_sheet_oct2025.csv` — Assets, liabilities, equity
- `debtors_age_oct2025.csv` — 8 customers, mix of current and overdue

Use realistic South African company names, rand amounts, and Pastel column formats.

**Add payroll sample files:**

- `payroll_summary_oct2025.csv` — 12 employees, mix of monthly and hourly staff
- `payroll_employee_cost_oct2025.csv` — full employer cost breakdown per employee
- `payroll_leave_liability_oct2025.csv` — leave balances (some employees with high balances)

Make one employee show a salary increase this month (triggers change alert).
Make leave liability total exceed 3 weeks of payroll (triggers warning).

-----

## CODING STANDARDS

- All Python functions must have type hints
- All API endpoints must have Pydantic request/response models
- All database queries through SQLAlchemy ORM (no raw SQL in API layer)
- Raw SQL only in `parsers/evolution_sql.py` and clearly commented
- Every Celery task must handle exceptions and update task status in DB
- Frontend: no `any` types in TypeScript
- All secrets via environment variables — never hardcoded
- Every file upload must be validated (type, size, basic format check)
- Log all LLM calls (model, tokens used, cost estimate, latency)

-----

## IMPORTANT NOTES FOR CLAUDE CODE

- This is a production product that will handle real client financial data
- Data privacy is critical — no client data should ever be logged in plain text
- The target users are non-technical SMB owners — all UI text must be plain English
- Report narratives must feel human and warm, not robotic or generic
- When in doubt about a metric calculation, use the conservative/cautious value
- Test all parsers against real Pastel export formats — they vary between versions
- The Evolution SQL queries assume standard Evolution table names — verify on first install
- WhatsApp messages must be under 1,024 characters for template messages
- PDF reports must print cleanly on A4 paper (client may print and file it)

-----

## NUMBERS10 BRANDING IN REPORTS

All PDF reports carry the Ghost CFO brand (powered by Numbers10):

- Header: Ghost CFO logo + company name + report period
- Footer: “Powered by Numbers10 Technology Solutions | numbers10.co.za”
- Colour: Teal accent (#2DD4BF) for headings and highlights
- Font: Inter for body, Space Grotesk for headings
- Page size: A4, portrait
- Include health score badge (colour-coded: green/amber/red)

-----

## PUBLIC WEBSITE — MARKETING LANDING PAGE

The root domain `ghostcfo.numbers10.co.za` is a **public marketing website first**.
It advertises Ghost CFO to prospective clients. The portal login is accessed from
a "Client Login" button in the top-right nav of the website.

### URL structure

```
/           → Public marketing website (no auth)
/login      → Portal login page
/dashboard  → Protected portal (auth required)
/upload     → Protected portal
/reports    → Protected portal
/settings   → Protected portal
/admin      → Protected portal (admin only)
```

### Website sections (in order)

1. **Navbar** — Logo + nav links + "Client Login" button (teal)
2. **Hero** — Full-viewport, dark background, large headline, subheadline, two CTAs
3. **Social proof strip** — "Trusted by SA businesses | Sage Pastel Integration | R500/month"
4. **How it works** — 3-step process (Connect → Auto-analyse → Receive report)
5. **Features** — 6 feature cards (plain-language narrative, PDF + WhatsApp, debtors, payroll, cash runway, health score)
6. **What the report looks like** — Mockup / preview of the actual output
7. **Pricing** — 3 plans (Starter R500, Professional R900, Premium R1500) with feature lists
8. **Pastel compatibility** — Evolution + Partner + Payroll logos/badges
9. **About** — Powered by Numbers10, years of Pastel experience, SA-focused
10. **CTA strip** — "Ready to know your numbers?" + Contact button
11. **Footer** — Links, Numbers10 branding, legal

### Website design rules

- Same brand as the portal: pure black background, teal-to-cyan gradient accent
- Space Grotesk for headings (very large on hero — 4xl to 6xl)
- Inter for body text, zinc-400 colour on dark
- Subtle gradient glow effects and animated gradient text on hero headline
- Pricing cards: highlight the Professional plan as "Most Popular"
- Mobile-responsive (hamburger menu on mobile)
- Tailwind CSS throughout — consistent with portal
- No images — use CSS, icons, and styled text blocks only (avoids asset dependencies)

-----

*Ghost CFO — CLAUDE.md v1.2 — Added public marketing website*
*Numbers10 Technology Solutions*
*Built with Claude Code*