# IMP-CRA Portal

**Integrity Management Program — Corruption Risk Assessment Portal**

A digital platform for the Philippine Government's Integrity Management Program (IMP), jointly implemented by the **Office of the President** and the **Office of the Ombudsman**.

The Portal digitizes the compliance, assessment, and reporting workflow that public sector institutions currently perform through paper-based templates under the IMP Handbook (2015). It replaces a fragmented, manual process with a structured, data-driven system aligned with Republic Act 6713, RA 9485 (ARTA), the United Nations Convention Against Corruption (UNCAC), and the six IMP dimensions.

---

## Table of Contents

- [Background](#background)
- [What the Portal Does](#what-the-portal-does)
- [The Six IMP Dimensions](#the-six-imp-dimensions)
- [Templates Implemented](#templates-implemented)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [Authentication Flow](#authentication-flow)
- [API Endpoints](#api-endpoints)
- [Roadmap](#roadmap)
- [Handbook Reference](#handbook-reference)
- [License](#license)

---

## Background

The Integrity Management Program (IMP) is the Philippine Government's flagship anti-corruption program. It adopts the framework of the **United Nations Convention Against Corruption (UNCAC)**, signed by the Philippines in December 2003 and ratified in November 2006.

The IMP harmonizes two earlier programs:

- **Integrity Development Review (IDR)** — a diagnostic tool to assess an institution's resistance and vulnerabilities to corruption (pilot-tested 2003, adopted by 22 agencies).
- **Integrity Development Action Plan (IDAP)** — the national anti-corruption framework of the executive branch (2004), composed of 22 anti-corruption measures.

Both were found by a 2012 Management Systems International (MSI) evaluation to have weak oversight, limited monitoring and evaluation, and indicators that were not agency-specific. The IMP was designed as a harmonized successor — outcome-based, flexible, and equipped with proper M&E and oversight mechanisms.

Each participating public sector institution establishes an **Integrity Management Committee (IMC)** and works through a five-stage management cycle:

1. Setting up an IMC
2. Conducting an Integrity Assessment
3. Developing an Integrity Management Plan
4. Implementing the Integrity Management Plan
5. Conducting Internal Monitoring and Evaluation

The Program Management Committee (PMC), supported by a Technical Secretariat from OP-ODESLA and the Ombudsman, oversees the entire process.

---

## What the Portal Does

The IMP-CRA Portal digitizes stages 2 through 5 of the institutional management cycle:

| Stage | Manual Process | Portal Equivalent |
|---|---|---|
| Integrity Assessment | Paper-based Templates 1–4 | Module 1 & 3 web forms |
| IMP Development | Word/Excel Templates 5–6 | (Phase 5, admin dashboard) |
| Implementation | Tracked in spreadsheets | (Phase 5) |
| Monitoring & Evaluation | Semestral reports, Template 8 | (Phase 6) |
| Reporting | Annual Template 9 + Rating Sheet | (Phase 6) |

**Target users:**

- **Client (Agency)** — IMC members from public sector institutions who conduct the assessment and maintain their Integrity Management Plan
- **Admin (PMC / Technical Secretariat)** — OP-ODESLA and Ombudsman staff who review submissions, evaluate performance, and manage certification

---

## The Six IMP Dimensions

Every integrity measure developed through the Portal belongs to one of the six dimensions defined in the IMP Handbook. The Portal enforces this categorization so reports can be aggregated consistently.

| # | Dimension | Desired Outcome |
|---|---|---|
| 1 | **Service Delivery** | Delivery of services and interaction with external stakeholders made responsive and more transparent |
| 2 | **Institutional Leadership** | Ethical leadership wherein integrity is visibly practiced and promoted by senior officials and middle managers |
| 3 | **Financial, Procurement & Asset Management** | All government resources are safeguarded against improper use, loss and wastage, and savings from efficient operations realized |
| 4 | **Human Resource Management & Development** | Employees are selected and promoted based on merit and fitness |
| 5 | **Corruption Risk Management** | Corruption control measures are proactively installed and implemented by accountable officers in identified corruption risk areas |
| 6 | **Internal Reporting & Investigation** | Breaches to integrity standards are detected, reported and penalized |

Each dimension maps values (RA 6713), governance principles (UNDP 2003), and standards (RA 9485, RA 9184, PD 1445, UNCAC articles) to actionable integrity measures.

---

## Templates Implemented

The IMP Handbook defines ten templates. The Portal implements the four most operationally critical ones in Phase 4.

| Template | Description | Portal Phase |
|---|---|---|
| **Template 1** | Critical Systems for Assessment | Phase 4 (Module 1) |
| **Template 2** | Process Matrix | Phase 4 (Module 1) |
| **Template 3** | Corruption Risk Register | Phase 4 (Module 3) |
| **Template 4** | Integrity Assessment Report | Phase 4 (Module 3) |
| Template 5 | IMP Logical Framework | Phase 5 |
| Template 6 | Implementation Plan | Phase 5 |
| Template 7 | Monitoring & Evaluation Plan | Phase 6 |
| Template 8 | M&E Progress Report | Phase 6 |
| Template 9 | Performance Monitoring Report | Phase 6 |
| Template 10 | Performance Rating Sheet | Phase 6 |

**The Corruption Risk Register (Template 3)** is the analytical heart of the Portal. Its scoring follows the IMP Handbook:

```
Probability (1-15)  +  Impact (1-15)
────────────────────────────────────  =  Inherent Risk
                  2

Band:  Low = 1-5   |   Medium = 6-10   |   High = 11-15
```

Residual risk is then derived by adjusting the inherent band based on the effectiveness of existing mitigating controls (High / Medium / Low).

---

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   React SPA         │         │   Turso Cloud        │
│   (Vite)            │         │   (libSQL / SQLite)  │
│                     │         │                      │
│  • Landing page     │         │  • users             │
│  • Magic-link auth  │         │  • agencies          │
│  • Protected routes │         │  • email_verifications│
│  • Assessment UI    │         │  • assessments       │
└──────────┬──────────┘         │  • processes         │
           │                    │  • risks             │
           │  /api/*            └──────────▲───────────┘
           │                               │
           ▼                               │ SQL over HTTPS
┌─────────────────────┐                    │
│  Python Serverless  │────────────────────┘
│  Functions          │
│                     │         ┌──────────────────────┐
│  • send_verification│────────▶│   Resend API         │
│  • verify_email     │  HTTPS  │   (transactional     │
│  • request_link     │         │    email)            │
│  • (assessment CRUD)│         └──────────────────────┘
└─────────────────────┘
```

**Local development** runs the frontend and API as two processes:

- `npx vite` — React on `http://localhost:3000`
- `python run_api.py` — Python API on `http://localhost:3001`

Vite proxies all `/api/*` requests to the Python server, so the frontend calls relative paths exactly as it would in production.

**Production** runs everything on Vercel:

- The React SPA builds to static assets
- `api/*.py` files deploy as individual serverless functions
- Turso and Resend are reached over HTTPS from those functions

---

## Tech Stack

**Frontend**
- React 18
- Vite 8
- React Router 6
- Vanilla CSS (no framework)

**Backend**
- Python 3.12 (Vercel runtime)
- `http.server.BaseHTTPRequestHandler` (no web framework)
- PyJWT (session tokens)
- Resend SDK (transactional email)

**Database**
- Turso Cloud (libSQL — SQLite at the edge)
- `turso-serverless` Python driver (pure HTTP, no native compilation)

**Infrastructure**
- Vercel (frontend + serverless functions)
- Turso (managed libSQL)
- Resend (email delivery)

---

## Project Structure

```
Project_CRA/
├── api/                            # Vercel serverless functions
│   ├── send_verification.py        # POST /api/send_verification
│   ├── verify_email.py             # POST /api/verify_email
│   ├── request_link.py             # POST /api/auth/request_link
│   └── (future) assessments.py, processes.py, risks.py
│
├── lib/                            # Shared backend utilities
│   ├── db.py                       # Turso connection helper
│   ├── auth.py                     # JWT minting / verification
│   └── magic_link.py               # Token gen + email templates
│
├── database/
│   └── init_db.py                  # Schema creation script
│
├── src/                            # React frontend
│   ├── main.jsx                    # Entry point
│   ├── App.jsx                     # Router + SessionProvider
│   ├── index.css                   # Global reset
│   ├── auth.css                    # Auth page styles
│   ├── assets/                     # Logos and background images
│   ├── components/
│   │   └── ProtectedRoute.jsx
│   ├── hooks/
│   │   └── useSession.jsx          # Session context + hook
│   ├── lib/
│   │   └── api.js                  # Fetch wrapper with auth header
│   └── pages/
│       ├── LandingPage.jsx         # Public landing page
│       ├── LandingPage.css
│       ├── Register.jsx
│       ├── Login.jsx
│       ├── Verify.jsx
│       └── Dashboard.jsx
│
├── run_api.py                      # Local dev API server (router)
├── vite.config.js                  # Vite + proxy config
├── requirements.txt                # Python dependencies
├── package.json
├── .env.local                      # Dev secrets (gitignored)
└── README.md
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.12+
- A Turso account ([turso.tech](https://turso.tech))
- A Resend account ([resend.com](https://resend.com))

### 1. Clone and install

```bash
git clone <your-repo-url>
cd Project_CRA

# Frontend
npm install

# Backend
pip install --user -r requirements.txt
```

### 2. Provision Turso

```bash
turso auth login
turso db create project-cra

# Get the URL and generate a token
turso db show project-cra --url
turso db tokens create project-cra
```

### 3. Configure `.env.local`

See [Environment Variables](#environment-variables) below.

### 4. Initialize the database

```bash
python database/init_db.py
```

Expected output: all tables (`assessments`, `processes`, `risks`, `email_verifications`, `users`, `agencies`) created successfully.

### 5. Run the dev servers

**Terminal 1 — Backend:**
```bash
python run_api.py
# → ✅ Python API server running at http://localhost:3001
```

**Terminal 2 — Frontend:**
```bash
npx vite
# → ➜  Local:   http://localhost:3000/
```

Open **http://localhost:3000**.

---

## Environment Variables

Create `.env.local` in the project root:

```bash
# ─── Email (Resend) ─────────────────────────────────────
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=IMP-CRA Portal <onboarding@resend.dev>

# ─── Session signing ────────────────────────────────────
# Generate with: openssl rand -hex 32
TOKEN_SECRET=<64-char-hex>
JWT_SECRET=<64-char-hex>

# ─── URLs ───────────────────────────────────────────────
# Single URL — used to build magic links in emails
APP_URL=http://localhost:3000

# Comma-separated list — used for CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# ─── Database (Turso) ───────────────────────────────────
TURSO_DATABASE_URL=libsql://project-cra-<org>.turso.io
TURSO_AUTH_TOKEN=<turso-token>
```

**Production values (Vercel → Settings → Environment Variables):**

```bash
APP_URL=https://project-cra.vercel.app
ALLOWED_ORIGINS=https://project-cra.vercel.app
# ... plus the same secrets as above
```

> **Never commit `.env.local`.** Confirm it's listed in `.gitignore`.

---

## Database Schema

### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `email` | TEXT NOT NULL UNIQUE | |
| `agency` | TEXT | Agency display name |
| `role` | TEXT NOT NULL DEFAULT 'client' | `'client'` or `'admin'` |
| `verified` | INTEGER NOT NULL DEFAULT 0 | Set to 1 after magic-link verification |
| `created_at` | TEXT | ISO8601 |

### `email_verifications`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `email` | TEXT NOT NULL | |
| `agency` | TEXT NOT NULL | |
| `token_hash` | TEXT NOT NULL UNIQUE | HMAC-SHA256 of the raw token |
| `expires_at` | TEXT NOT NULL | ISO8601 UTC, TTL = 30 minutes |
| `used_at` | TEXT | Set when consumed; NULL if unused |
| `created_at` | TEXT | |

### `assessments`

| Column | Type | Notes |
|---|---|---|
| `assessment_id` | TEXT PK | |
| `agency_name` | TEXT | |
| `assessment_profile` | TEXT | |
| `status` | TEXT | `'draft'`, `'submitted'`, `'under_review'`, `'certified'` |
| `client_id` | TEXT | FK to `users.id` (added via migration) |

### `processes` *(Template 2 backbone)*

| Column | Type |
|---|---|
| `process_id` | TEXT PK |
| `assessment_id` | TEXT FK |
| `process_name` | TEXT |
| `screening_rationale` | TEXT |
| `is_selected` | BOOLEAN |

### `risks` *(Template 3)*

| Column | Type |
|---|---|
| `risk_id` | TEXT PK |
| `process_id` | TEXT FK |
| `event_statement` | TEXT |
| `inherent_likelihood` | INTEGER (1–15) |
| `inherent_consequence` | INTEGER (1–15) |
| `inherent_risk_level` | TEXT (`'H'`, `'M'`, `'L'`) |
| `risk_owner` | TEXT |

### `agencies`

| Column | Type |
|---|---|
| `id` | INTEGER PK AUTOINCREMENT |
| `name` | TEXT NOT NULL UNIQUE |
| `created_at` | TEXT |

---

## Authentication Flow

The Portal uses **magic-link authentication** — no passwords, no third-party OAuth. This matches the government's preference for controlled email domains and reduces the attack surface.

```
NEW USER
  ┌─────────────────────────────────────────────────────┐
  │ 1. POST /api/send_verification { email, agency }    │
  │    → Server stores HMAC(token) in email_verifications│
  │    → Resend delivers raw token via email link       │
  └─────────────────────────┬───────────────────────────┘
                            ▼
  ┌─────────────────────────────────────────────────────┐
  │ 2. User clicks link → /verify?token=<raw>           │
  │    React POSTs raw token to /api/verify_email       │
  │    → Server matches against stored HMAC hash        │
  │    → Validates expiry + used_at                     │
  │    → Upserts user row (verified = 1)                │
  │    → Mints HS256 JWT (30-day TTL)                   │
  └─────────────────────────┬───────────────────────────┘
                            ▼
  ┌─────────────────────────────────────────────────────┐
  │ 3. Frontend stores JWT in localStorage              │
  │    → SessionProvider decodes exp                    │
  │    → All API calls include Authorization: Bearer    │
  │    → ProtectedRoute allows access to /dashboard     │
  └─────────────────────────────────────────────────────┘

RETURNING USER
  POST /api/auth/request_link { email } → same flow
  (endpoint is privacy-preserving: always returns 'sent')
```

**Security properties:**

- Raw tokens are never stored — only their HMAC-SHA256 hash
- Tokens are single-use (`used_at` marks consumption)
- Tokens expire after 30 minutes
- 60-second cooldown between link requests per email
- JWTs are HS256-signed with a 32-byte secret, expire after 30 days
- API responses don't leak whether an email exists

---

## API Endpoints

### `POST /api/send_verification`

Register a new agency and send a magic link.

**Request:**
```json
{ "email": "user@agency.gov.ph", "agency": "NCPAG" }
```

**Responses:**
- `200 {"status": "sent"}` — email sent
- `409 {"error": "already_registered"}` — direct user to `/login`
- `429 {"error": "rate_limited", "retry_after": 42}`

### `POST /api/verify_email`

Consume a token and mint a session.

**Request:**
```json
{ "token": "<raw-token-from-email>" }
```

**Response:**
```json
{
  "status": "verified",
  "token": "eyJhbGc...",
  "user": {
    "id": 1,
    "email": "user@agency.gov.ph",
    "agency": "NCPAG",
    "role": "client",
    "verified": 1
  }
}
```

**Errors:** `invalid_token`, `already_used`, `expired`, `missing_token`

### `POST /api/auth/request_link`

Send a new sign-in link to an existing user.

**Request:**
```json
{ "email": "user@agency.gov.ph" }
```

**Response:** `200 {"status": "sent"}` (always, regardless of whether the email exists)

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| **1. Environment & Architecture** | Vercel serverless, Pop!_OS local setup, Turso provisioning | ✅ Complete |
| **2. Landing Page** | Cinematic public entry point | ✅ Complete |
| **3. Identity & Access Management** | Role-based users, magic-link auth, email verification | ✅ Complete |
| **4. Client Dashboard** | Agency-specific assessment views (Templates 1–4) | 🚧 In progress |
| **5. Admin Dashboard** | PMC/Technical Secretariat oversight command center | Planned |
| **6. Reporting & Analytics** | Template 9 Performance Monitoring Report export | Planned |
| **7. Security & Operations** | API input validation, technical documentation handover | Planned |

**Phase 4 breakdown:**

- [ ] Module 1 — Integrity Assessment (Templates 1 & 2)
- [ ] Module 3 — Corruption Risk Register (Template 3)
- [ ] Template 4 — Assessment Report generator

---

## Handbook Reference

This Portal implements the procedures defined in:

> **Integrity Management Program Handbook: Building a Culture of Integrity**
> A joint project of the Office of the President and the Office of the Ombudsman (2015)

Key sections:

- **Part I** — Program overview, six dimensions, implementing structures
- **Part II** — IMP implementation guide (IMC setup, integrity assessment, plan development)
- **Part III** — Program monitoring and evaluation (Progress Reports, Performance Ratings, Certification)
- **Annex 1** — Guidelines on CSO Participation

**Legal basis:**

- RA 6713 — Code of Conduct and Ethical Standards for Public Officials and Employees
- RA 9485 — Anti-Red Tape Act (ARTA)
- RA 9184 — Government Procurement Reform Act
- RA 3019 — Anti-Graft and Corrupt Practices Act
- PD 1445 — Government Auditing Code of the Philippines
- EO 176, s. 2014 — Institutionalizing the Integrity Management Program
- UNCAC — United Nations Convention Against Corruption (ratified 2006)

---

## License

Government of the Republic of the Philippines. Joint project of the Office of the President, Office of the Ombudsman and the UP-NCPAG GRIT Labs.