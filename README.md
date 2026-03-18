# AskAI — AI Knowledge Platform

A local LLM-powered knowledge platform that lets you chat with your company's documents, FAQ, and structured database data. Built with FastAPI, Next.js, PostgreSQL, and Ollama.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Local Setup](#local-setup)
6. [How to Run](#how-to-run)
7. [Default Accounts](#default-accounts)
8. [Features & How to Test](#features--how-to-test)
9. [API Endpoints](#api-endpoints)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                │
│            http://localhost:3000                     │
│  Login → Dashboard → Assistant → Admin Pages        │
└──────────────────────┬──────────────────────────────┘
                       │ API calls via /api proxy
┌──────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                   │
│             http://localhost:8000                    │
│                                                     │
│  ┌─────────┐ ┌──────────┐ ┌───────────────────┐    │
│  │  Auth   │ │  CRUD    │ │  Unified Query    │    │
│  │  (JWT)  │ │  APIs    │ │  Engine           │    │
│  └─────────┘ └──────────┘ │  ┌─────────────┐  │    │
│                            │  │ FAQ Search  │  │    │
│                            │  │ Doc Search  │  │    │
│                            │  │ Text-to-SQL │  │    │
│                            │  └──────┬──────┘  │    │
│                            └─────────┼─────────┘    │
└──────────────┬───────────────────────┼──────────────┘
               │                       │
    ┌──────────▼──────────┐  ┌─────────▼─────────┐
    │   PostgreSQL 18     │  │    Ollama (Local)  │
    │   Database: askai   │  │    llama3 (chat)   │
    │                     │  │    nomic-embed-text │
    │   10 tables         │  │    (embeddings)    │
    │   + dynamic tables  │  │                    │
    │     from CSV upload │  │  localhost:11434   │
    └─────────────────────┘  └────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS 4 | Web UI with App Router |
| **Backend** | FastAPI, Python 3.12, Uvicorn | REST API server |
| **Database** | PostgreSQL 18, SQLAlchemy (async), Alembic | Data storage + migrations |
| **LLM** | Ollama, Llama 3 8B | Chat, answer generation, Text-to-SQL |
| **Embeddings** | nomic-embed-text (via Ollama) | Document similarity search |
| **Auth** | JWT (python-jose), bcrypt (passlib) | Authentication & authorization |
| **Background** | Celery + Redis | PDF processing, CSV import jobs |
| **Icons** | lucide-react | UI icons |

---

## Project Structure

```
local_llm/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app entry point
│   │   ├── core/
│   │   │   ├── config.py        ← Settings (from .env)
│   │   │   ├── database.py      ← Async SQLAlchemy engine
│   │   │   ├── security.py      ← JWT + password hashing
│   │   │   ├── dependencies.py  ← Role-based access guards
│   │   │   └── logger.py        ← Logging config
│   │   ├── models/              ← SQLAlchemy ORM models
│   │   │   ├── company.py
│   │   │   ├── user.py
│   │   │   ├── document.py      ← Document + DocumentChunk
│   │   │   ├── faq.py
│   │   │   ├── dataset.py       ← Dataset + DatasetImport
│   │   │   ├── chat.py          ← ChatSession + ChatMessage
│   │   │   └── audit.py
│   │   ├── schemas/             ← Pydantic request/response models
│   │   ├── api/                 ← FastAPI route handlers
│   │   │   ├── auth.py          ← Login, /me
│   │   │   ├── companies.py     ← Company CRUD
│   │   │   ├── users.py         ← User CRUD
│   │   │   ├── documents.py     ← PDF upload/delete
│   │   │   ├── faq.py           ← FAQ CRUD
│   │   │   ├── datasets.py      ← Table creation, CSV import
│   │   │   ├── chat.py          ← Chat sessions + unified query
│   │   │   └── audit.py         ← Audit log listing
│   │   ├── services/            ← Business logic
│   │   ├── llm/
│   │   │   ├── ollama_client.py ← Ollama HTTP client
│   │   │   ├── unified_query.py ← Searches FAQ + docs + DB, calls LLM
│   │   │   └── prompts/         ← System prompts
│   │   └── ingestion/
│   │       ├── pdf_parser.py    ← PyMuPDF text extraction + chunking
│   │       └── csv_importer.py  ← CSV schema inference
│   ├── alembic/                 ← Database migrations
│   ├── requirements.txt
│   └── venv/                    ← Python virtual environment
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       ← Root layout with AuthProvider
│   │   │   ├── page.tsx         ← Redirect to /dashboard
│   │   │   ├── login/page.tsx   ← Login screen
│   │   │   └── dashboard/
│   │   │       ├── layout.tsx   ← Sidebar + Topbar + company switcher
│   │   │       ├── page.tsx     ← Overview / home
│   │   │       ├── assistant/   ← Chat interface
│   │   │       ├── documents/   ← PDF upload & management
│   │   │       ├── faq/         ← FAQ management
│   │   │       ├── database/    ← Table creation & CSV import
│   │   │       ├── companies/   ← Company management
│   │   │       ├── users/       ← User management
│   │   │       └── audit/       ← Audit logs
│   │   ├── components/layout/   ← Sidebar.tsx, Topbar.tsx
│   │   ├── hooks/               ← useCompanyId.ts
│   │   └── lib/
│   │       ├── api.ts           ← API client (fetch wrapper)
│   │       ├── auth-context.tsx ← React auth context + JWT
│   │       └── types.ts         ← TypeScript interfaces
│   ├── package.json
│   └── next.config.ts           ← API proxy to backend
│
├── storage/
│   └── uploads/companies/       ← File storage per company
│
├── .env                         ← Environment config
├── .env.example                 ← Template
└── .gitignore
```

---

## Prerequisites

These must be installed and running on your machine:

| Requirement | Version | Check Command |
|------------|---------|--------------|
| **Node.js** | 22+ | `node --version` |
| **Python** | 3.12+ | `python --version` |
| **PostgreSQL** | 18 | `psql --version` |
| **Ollama** | 0.17+ | Check at http://localhost:11434 |
| **Redis** | any | `docker ps` (runs in Docker) |
| **Docker** | 28+ | `docker --version` |
| **pnpm** | 10+ | `pnpm --version` |
| **Git** | 2.49+ | `git --version` |

### Ollama Models Required

| Model | Size | Purpose |
|-------|------|---------|
| `llama3` | ~4.7 GB | Chat, answer generation, SQL generation |
| `nomic-embed-text` | ~274 MB | Document embedding for similarity search |

Pull them with:
```bash
ollama pull llama3
ollama pull nomic-embed-text
```

---

## Local Setup

### 1. Database

The PostgreSQL database `askai` should already exist. If not:

```sql
-- Connect to PostgreSQL as postgres user
CREATE DATABASE askai;
\c askai
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 2. Redis (via Docker)

```bash
docker run -d --name redis -p 6379:6379 redis:alpine
```

### 3. Backend

```bash
cd backend

# Activate virtual environment
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Mac/Linux

# Run database migrations
python -m alembic upgrade head

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will:
- Create all database tables if they don't exist
- Create the super admin account on first startup
- Be available at http://localhost:8000
- API docs at http://localhost:8000/docs (Swagger UI)

### 4. Frontend

```bash
cd frontend

# Install dependencies (if not done)
pnpm install

# Start dev server
pnpm dev
```

Frontend available at http://localhost:3000

### 5. Ollama

Make sure Ollama is running (it starts automatically on install). Verify:
```bash
curl http://localhost:11434/api/tags
```

---

## How to Run

**Start all services (3 terminals):**

```
# Terminal 1 — Backend
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd frontend
pnpm dev

# Terminal 3 — Redis (if not running)
docker start redis
```

Then open http://localhost:3000 in your browser.

---

## Default Accounts

| Email | Password | Role | Company |
|-------|----------|------|---------|
| `admin@askai.local` | `admin123` | Super Admin | — (platform-wide access) |
| `user@demo.com` | `demo123` | Admin | Demo Company |

### Role Permissions

| Feature | User | Admin | Super Admin |
|---------|------|-------|-------------|
| Chat with assistant | ✅ | ✅ | ✅ |
| View documents/FAQ | ✅ | ✅ | ✅ |
| Upload documents | ❌ | ✅ | ✅ |
| Manage FAQ | ❌ | ✅ | ✅ |
| Manage database/tables | ❌ | ✅ | ✅ |
| Manage companies | ❌ | ❌ | ✅ |
| Manage users | ❌ | ✅ (own company) | ✅ (all) |
| View audit logs | ❌ | ✅ (own company) | ✅ (all) |

---

## Features & How to Test

### Test 1: Login

1. Go to http://localhost:3000
2. You will be redirected to the login page
3. Enter `admin@askai.local` / `admin123`
4. You should see the Dashboard with Overview page

### Test 2: Create a Company

1. Login as `admin@askai.local` (super admin)
2. Click **Companies** in the sidebar (under Platform)
3. Click **Add Company**
4. Enter name: "My Test Company", click Create
5. The company appears in the table

### Test 3: Create a User

1. Click **Users** in the sidebar (under Platform)
2. Click **Add User**
3. Fill in:
   - Full Name: `John Doe`
   - Email: `john@test.com`
   - Password: `test123`
   - Role: `admin` (or `user`)
   - Company: select "My Test Company" (or "Demo Company")
4. Click **Create User**
5. The user appears in the table
6. You can now logout and login as this new user

### Test 4: Add FAQ Items

1. Login as an admin user (e.g., `user@demo.com` / `demo123`)
2. Click **FAQ** in the sidebar (under Administration)
3. Click **Add FAQ**
4. Enter:
   - Question: `What is the return policy?`
   - Answer: `You can return any item within 30 days of purchase with a valid receipt.`
   - Category: `Policy`
5. Click **Save**
6. Add a few more FAQ items

### Test 5: Chat with the Assistant

1. Click **Assistant** in the sidebar
2. Type: `What is the return policy?`
3. Press Enter or click Send
4. The system will:
   - Search FAQ items (keyword match) → finds your FAQ entry
   - Search uploaded documents (none yet)
   - Search database tables (none yet)
   - Call Ollama llama3 to generate a combined answer
5. The response should reference the FAQ you added
6. You'll see source indicators (FAQ matches, etc.) below the answer

### Test 6: Upload a PDF Document

1. Click **Documents** in the sidebar
2. Click **Upload PDF**
3. Select any PDF file
4. The document appears in the table with status "pending"
5. (Full PDF processing with chunking + embedding will be added in a future update)

### Test 7: Create a Database Table from CSV

1. Click **Database** in the sidebar
2. Click the **Upload Table & Data** tab
3. Enter Display Name: `Sales Report`
4. Select a CSV file (any CSV with headers)
5. A preview of columns and data will appear
6. Click **Create Table & Import**
7. Switch to the **Tables** tab to see your new table
8. Now in the Assistant, ask: `What is the total sales?` — the system will try to generate SQL to query your table

### Test 8: Create a Table Manually

1. In the Database page, click **Create Table** tab
2. Enter Table Name: `Products`
3. Add columns:
   - `name` (Text)
   - `price` (Float)
   - `quantity` (Integer)
4. Click **Create Table**
5. Then use **Upload Data** tab to import CSV data into this table

### Test 9: Company Switcher (Super Admin)

1. Login as `admin@askai.local`
2. In the topbar, you'll see a company dropdown
3. Select different companies to scope the administration pages
4. Documents, FAQ, and Database pages will show data for the selected company

### Test 10: Audit Logs

1. Click **Audit Logs** in the sidebar (under Platform)
2. You'll see a log of all actions: logins, company creation, user creation, uploads, etc.

---

## API Endpoints

The backend exposes a REST API. Full interactive docs available at http://localhost:8000/docs

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login (OAuth2 form) |
| GET | `/api/auth/me` | Get current user |

### Companies (Super Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/companies` | List all companies |
| POST | `/api/companies` | Create company |
| GET | `/api/companies/{id}` | Get company |
| PATCH | `/api/companies/{id}` | Update company |

### Users (Admin+)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | List users |
| POST | `/api/users` | Create user |
| PATCH | `/api/users/{id}` | Update user |

### Documents (Admin+)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/{company_id}` | List documents |
| POST | `/api/documents/{company_id}` | Upload PDF |
| DELETE | `/api/documents/{company_id}/{doc_id}` | Delete document |

### FAQ (Admin+)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faq/{company_id}` | List FAQ |
| POST | `/api/faq/{company_id}` | Create FAQ |
| PATCH | `/api/faq/{company_id}/{faq_id}` | Update FAQ |
| DELETE | `/api/faq/{company_id}/{faq_id}` | Delete FAQ |

### Datasets (Admin+)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/datasets/{company_id}` | List datasets |
| POST | `/api/datasets/{company_id}/manual` | Create table manually |
| POST | `/api/datasets/{company_id}/upload-table` | Upload CSV → create table + data |
| POST | `/api/datasets/{company_id}/{id}/upload-data` | Import CSV into existing table |
| POST | `/api/datasets/{company_id}/preview-csv` | Preview CSV before import |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/sessions` | List chat sessions |
| GET | `/api/chat/sessions/{id}/messages` | Get messages |
| POST | `/api/chat` | Send message (unified query) |
| DELETE | `/api/chat/sessions/{id}` | Delete session |

### Audit (Admin+)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit` | List audit logs |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

---

## Troubleshooting

### Backend won't start
- **Port 8000 in use**: `netstat -ano | findstr :8000` then `Stop-Process -Id <PID> -Force`
- **Module not found**: Make sure you activated the venv: `.\venv\Scripts\activate`
- **Database connection error**: Check PostgreSQL is running: `Get-Service postgresql*`

### Frontend won't start
- **Port 3000 in use**: `netstat -ano | findstr :3000` then `Stop-Process -Id <PID> -Force`
- **Module not found**: Run `pnpm install` in the `frontend/` directory

### Login fails
- Default super admin: `admin@askai.local` / `admin123`
- If no users exist, restart the backend — it creates the super admin on startup

### Chat returns "LLM offline"
- Make sure Ollama is running: visit http://localhost:11434
- Check models are pulled: `ollama list`
- The backend connects to Ollama at `http://localhost:11434` (configurable in `.env`)

### Chat returns "no relevant information"
- You need to add data first: upload FAQ items, documents, or CSV tables
- FAQ items are matched by keywords immediately
- For smarter matching, Ollama must be running

### CSV upload fails
- Make sure the CSV has headers in the first row
- Only `.csv` files are accepted
- Check the file isn't empty

### Company switcher is empty
- Only super admins see the company switcher
- You need to create companies first (Platform → Companies)

### bcrypt warning on startup
```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```
This is a known passlib/bcrypt compatibility warning. It's harmless — authentication works fine.

---

## Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:920214@localhost:5432/askai` | Async DB connection |
| `DATABASE_URL_SYNC` | `postgresql+psycopg2://postgres:920214@localhost:5432/askai` | Sync DB connection (Alembic) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `SECRET_KEY` | (dev key) | JWT signing secret |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `LLM_MODEL` | `llama3` | Chat model |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `FRONTEND_URL` | `http://localhost:3000` | CORS allowed origin |
| `SUPER_ADMIN_EMAIL` | `admin@askai.local` | Auto-created super admin |
| `SUPER_ADMIN_PASSWORD` | `admin123` | Super admin password |

---

## What's Been Built (v0.1)

### Backend
- ✅ FastAPI REST API with 8 route modules
- ✅ JWT authentication with role-based access control (super_admin, admin, user)
- ✅ 10 database tables with Alembic migrations
- ✅ Company multi-tenancy with row-level isolation (company_id)
- ✅ PDF upload with file storage per company
- ✅ CSV upload → auto-create PostgreSQL table + insert data
- ✅ Manual table creation with custom columns
- ✅ Unified query engine (FAQ search + document search + Text-to-SQL)
- ✅ Ollama integration for LLM chat and SQL generation
- ✅ Audit logging for all admin actions
- ✅ Super admin auto-creation on startup

### Frontend
- ✅ Next.js 15 with App Router, TypeScript, Tailwind CSS 4
- ✅ Login page with dark gradient theme
- ✅ Dashboard with sidebar navigation (Main / Administration / Platform)
- ✅ Company switcher dropdown (super admin)
- ✅ 8 pages: Overview, Assistant, Documents, FAQ, Database, Companies, Users, Audit
- ✅ Chat interface with session management, source display, SQL display
- ✅ Database page with 4 tabs (Tables, Create, Upload Table, Upload Data)
- ✅ API proxy to backend via Next.js rewrites

### Not Yet Built (Future)
- ⬜ Full PDF processing pipeline (parse → chunk → embed → store vectors)
- ⬜ Semantic search using embeddings (currently keyword-based)
- ⬜ Background job queue (Celery workers for PDF/CSV processing)
- ⬜ Password change / forgot password
- ⬜ File size limits and validation
- ⬜ Export data
- ⬜ Production deployment (Cloudflare Tunnel, systemd services)
