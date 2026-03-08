# AI Knowledge Assistant Platform — Technical Documentation

Version: 1.0  
Status: Development Specification  
Target deployment: Mac mini home server first, non-Docker, future Linux VPS migration  
Primary audience: Developer / technical implementer

---

## 1. Purpose

This document defines the full technical specification for building a multi-tenant AI knowledge assistant platform for companies in Malaysia.

The platform is intended to help staff ask natural-language questions and receive grounded answers from:
- curated FAQs
- uploaded PDF documents such as SOPs, manuals, policies, and procedures
- structured data imported from CSV files

The system must work for non-technical end users. They should not need to know whether the answer comes from FAQ, RAG, or structured data.

The first deployment target is a **Mac mini** running on home internet. The system must also be designed so it can later be moved to a **Linux VPS** with minimal code changes.

---

## 2. Product Summary

### 2.1 What the platform does

A company uploads:
- FAQs
- SOPs / manuals / policy PDFs
- CSV datasets

Then company users can log in and ask questions like:
- "What form should I use for incident reporting?"
- "What should I do during an aircraft emergency?"
- "How many pending reports are still open?"
- "Which section of the procedure explains this case?"

The system automatically:
1. identifies the tenant/company
2. searches the company’s FAQ
3. searches the company’s PDF knowledge base
4. checks whether structured data is needed
5. runs safe SQL only when appropriate
6. merges evidence
7. generates a grounded answer with citations
8. stores logs for audit and review

### 2.2 Core product positioning

This is **not just a chatbot**.

It is a **multi-tenant knowledge operations platform** for internal support, customer service, SOP guidance, and procedure lookup.

### 2.3 Example use cases

- airport operations support
- incident response guidance
- customer service knowledge assistant
- HR policy assistant
- finance or operations FAQ assistant
- internal reporting and form selection assistant

---

## 3. Scope

### 3.1 In scope for v1

- multi-tenant shared platform with row-level tenant isolation
- 2 user roles only: Super Admin and Standard User
- company creation by Super Admin
- user creation and assignment by Super Admin
- CSV upload and structured data import
- PDF upload and vector indexing
- FAQ management
- hybrid question answering across FAQ + RAG + structured data
- local LLM inference only
- Mac mini deployment without Docker
- Cloudflare Tunnel exposure for public access
- future Linux VPS migration design
- audit logging
- answer citations

### 3.2 Out of scope for v1

- public sign-up
- billing system
- separate Company Admin role
- SSO
- mobile app
- real-time collaboration
- workflow automation engine
- multilingual answer optimization beyond basic model capability
- external API marketplace
- image understanding
- direct editing of uploaded office documents in browser

---

## 4. User Roles

### 4.1 Super Admin

The Super Admin combines all administrative functions.

Permissions:
- create companies
- manage users for any company
- upload and manage CSV/PDF/FAQ
- view logs and audit trail
- review answers and source usage
- archive or deactivate content
- configure model settings and retrieval rules

### 4.2 Standard User

Permissions:
- log in
- ask questions
- view answers and citations
- give answer feedback
- access only data belonging to their assigned company

---

## 5. High-Level Architecture

```text
[User Browser]
      |
      v
[Next.js Frontend]
      |
      v
[FastAPI Backend]
      |
      +----------------------+---------------------+----------------------+
      |                      |                     |                      |
      v                      v                     v                      v
 [Auth & Tenant]      [Chat Orchestrator]   [Admin/Ingestion]      [Audit Logger]
                             |
        +--------------------+------------------------+------------------+
        |                    |                        |                  |
        v                    v                        v                  v
   [FAQ Retriever]    [Document Retriever]   [Structured Data Planner] [Answer Builder]
        |                    |                        |
        v                    v                        v
   [FAQ tables]   [Documents + Chunks + pgvector]   [PostgreSQL tenant data]
                                                                 |
                                                                 v
                                                        [Safe SQL Executor]

Additional services:
- Redis: queue/cache
- Worker: background ingestion tasks
- MinIO: file/object storage
- Ollama: local LLM and embedding inference
- Caddy/Nginx: reverse proxy
- cloudflared: tunnel for public access
```

---

## 6. Deployment Target

## 6.1 Primary target: Mac mini

The first production host is a Mac mini running at home.

Requirements:
- always-on machine
- stable local network
- enough disk for PDFs, CSVs, embeddings, logs, and model files
- tunnel-based public exposure
- local self-hosted LLM

## 6.2 Future target: Linux VPS

The same application must later be movable to a Linux VPS.

Migration should not require major redesign. Only infrastructure/service startup should change.

### 6.3 Why no Docker

This version is intentionally designed **without Docker**.

The stack will run as native services/processes.

Reasons:
- simpler setup for a single primary machine
- easier direct access to files and logs
- reduced container complexity
- suitable for Mac mini-first deployment

---

## 7. Non-Functional Requirements

### 7.1 Security
- strict tenant isolation by `company_id`
- server-side authorization only
- secure password hashing
- HTTPS via Cloudflare + reverse proxy
- no direct public database exposure
- safe SQL execution rules
- audit logs for uploads, queries, and answers

### 7.2 Reliability
- app services restart automatically where possible
- health endpoints for core services
- structured logging
- regular backups of DB and MinIO files

### 7.3 Performance
- good interactive response for normal business questions
- parallel retrieval where possible
- SQL only executed when needed
- background ingestion for heavy indexing tasks

### 7.4 Maintainability
- modular service structure
- clear interfaces between retrieval, ingestion, and answer generation
- environment-based configuration
- code portable to Linux VPS later

### 7.5 Usability
- non-technical users must ask questions naturally
- no need to select "FAQ" or "PDF" or "Database"
- answer should include source references when possible

---

## 8. Technology Stack

### 8.1 Frontend
- Next.js (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query

### 8.2 Backend
- FastAPI
- Python 3.11+
- Pydantic
- SQLAlchemy 2.x
- Alembic for migrations

### 8.3 Database
- PostgreSQL
- pgvector extension

### 8.4 Queue and worker
- Redis
- Python worker process (RQ, Dramatiq, or Celery alternative; recommended: RQ or Dramatiq for simplicity)

### 8.5 File storage
- MinIO
- local hard disk-backed object storage

### 8.6 LLM layer
- Ollama for chat and embeddings
- model provider abstraction in backend

### 8.7 Reverse proxy / edge
- Caddy or Nginx
- Cloudflare Tunnel (`cloudflared`) for public access
- optional Tailscale for private admin access

### 8.8 Observability
- application logs to file + stdout
- optional Sentry later
- optional Prometheus/Grafana later

---

## 9. Recommended Runtime Services

The following services run as separate native processes.

### 9.1 Required services
- `frontend` → Next.js app
- `api` → FastAPI backend
- `worker` → background jobs
- `postgresql` → DB
- `redis` → queue/cache
- `minio` → object storage
- `ollama` → local model inference
- `caddy` or `nginx` → reverse proxy
- `cloudflared` → public tunnel

### 9.2 Optional services
- `pgadmin` or Adminer equivalent, private only
- `tailscaled`
- monitoring stack later

---

## 10. Suggested Port Layout

Suggested internal ports on Mac mini:

- Next.js frontend: `3000`
- FastAPI backend: `8000`
- Ollama: `11434`
- Redis: `6379`
- PostgreSQL: `5432`
- MinIO API: `9000`
- MinIO console: `9001`
- Caddy/Nginx: `80` / `443` locally, or internal reverse proxy target

Note: public access should go through Cloudflare Tunnel rather than direct router port forwarding.

---

## 11. Domain Design

Recommended domain structure:
- `app.yourdomain.com` → frontend
- `api.yourdomain.com` → optional direct backend exposure if needed
- `admin.yourdomain.com` → optional future admin UI

For home deployment:
1. domain points to Cloudflare
2. Cloudflare Tunnel routes to local reverse proxy
3. reverse proxy routes to frontend and backend

For VPS deployment later:
1. keep same domain/subdomains
2. change Cloudflare origin to VPS
3. keep app logic unchanged

---

## 12. Codebase Structure

Recommended monorepo layout:

```text
project-root/
├─ frontend/
│  ├─ app/
│  ├─ components/
│  ├─ lib/
│  ├─ hooks/
│  ├─ styles/
│  └─ package.json
│
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ db/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  ├─ retrievers/
│  │  ├─ llm/
│  │  ├─ workers/
│  │  └─ main.py
│  ├─ alembic/
│  ├─ tests/
│  └─ requirements.txt
│
├─ worker/
│  └─ entrypoints or scripts if separated
│
├─ infra/
│  ├─ caddy/
│  ├─ nginx/
│  ├─ systemd/
│  ├─ cloudflared/
│  ├─ scripts/
│  └─ env/
│
├─ docs/
│  ├─ api/
│  ├─ architecture/
│  └─ runbooks/
│
└─ README.md
```

---

## 13. Multi-Tenancy Design

## 13.1 Tenant isolation model

Use **row-level tenant isolation**.

All tenant-owned records must include `company_id`.

The backend must enforce that every query is scoped to the logged-in user's `company_id`, unless the user is a true platform-level Super Admin operating through explicit administrative paths.

## 13.2 Required tenant rules

- never trust frontend for company scoping
- backend derives tenant context from authenticated session/token
- every repository/service method must accept tenant context explicitly
- every retrieval/search/SQL call must be filtered by `company_id`
- every vector/document chunk must include `company_id`

## 13.3 Tenant-aware coding rule

No DB query touching tenant data may be written without a tenant filter.

Bad:
```python
session.query(Document).filter(Document.status == 'active')
```

Good:
```python
session.query(Document).filter(
    Document.company_id == current_company_id,
    Document.status == 'active'
)
```

---

## 14. Authentication and Authorization

## 14.1 Authentication

Recommended v1 auth:
- email + password
- JWT access token + refresh token, or secure cookie session

Recommended backend responsibilities:
- password hashing with Argon2 or bcrypt
- short-lived access token
- refresh token rotation or secure session storage
- account status checks

## 14.2 Authorization

Role-based access control:
- Super Admin
- Standard User

Backend checks:
- role
- company membership
- account status
- resource ownership/company match

## 14.3 Session context

Each authenticated request should provide the backend with:
- `user_id`
- `company_id`
- `role`

These values should be derived from the token/session, not from request body headers.

---

## 15. Data Model Overview

This section defines the core logical entities.

### 15.1 Core tables

#### companies
- id
- name
- slug
- status
- created_at
- updated_at

#### users
- id
- company_id
- email
- full_name
- password_hash
- role
- status
- last_login_at
- created_at
- updated_at

#### faq_items
- id
- company_id
- question
- answer
- category
- tags
- priority
- status (`draft`, `approved`, `archived`)
- created_by
- created_at
- updated_at

#### documents
- id
- company_id
- title
- file_name
- object_key
- mime_type
- category
- department
- version_label
- status (`draft`, `approved`, `archived`)
- uploaded_by
- created_at
- updated_at

#### document_chunks
- id
- company_id
- document_id
- page_no
- section_title
- chunk_index
- content
- embedding (vector)
- token_count
- created_at

#### datasets
- id
- company_id
- name
- description
- source_type (`csv`)
- status
- created_by
- created_at
- updated_at

#### dataset_versions
- id
- company_id
- dataset_id
- version_no
- file_name
- object_key
- import_status
- row_count
- imported_at
- imported_by

#### dataset_columns
- id
- company_id
- dataset_id
- version_id
- column_name
- normalized_name
- data_type
- is_nullable
- description
- created_at

#### dataset_rows (option A if generic model)
- id
- company_id
- dataset_id
- version_id
- row_data JSONB
- created_at

#### import_jobs
- id
- company_id
- dataset_id
- version_id
- job_type (`csv_import`, `pdf_index`)
- status
- error_message
- created_by
- created_at
- started_at
- finished_at

#### chat_sessions
- id
- company_id
- user_id
- title
- created_at
- updated_at

#### chat_messages
- id
- company_id
- session_id
- user_id nullable
- role (`user`, `assistant`, `system`)
- content
- model_name
- created_at

#### answer_sources
- id
- company_id
- message_id
- source_type (`faq`, `document_chunk`, `sql_result`)
- source_ref_id
- relevance_score
- excerpt
- created_at

#### sql_query_logs
- id
- company_id
- user_id
- session_id
- prompt_text
- generated_sql
- executed_sql
- status
- row_count
- latency_ms
- error_message
- created_at

#### audit_logs
- id
- company_id nullable
- user_id nullable
- action
- entity_type
- entity_id
- metadata JSONB
- created_at

#### feedback
- id
- company_id
- message_id
- user_id
- rating
- comment
- created_at

---

## 16. Structured Data Storage Strategy

There are two possible implementation approaches for CSV-imported data.

### 16.1 Option A: generic JSONB row storage

Pros:
- easiest ingestion
- flexible for varying schemas

Cons:
- weaker SQL generation quality
- harder analytics
- weaker performance for complex filtering

### 16.2 Option B: managed generated tables

Pros:
- better SQL performance
- better text-to-SQL accuracy
- cleaner analytics

Cons:
- more engineering work

## 16.3 Recommended approach

For this product, use **Option B: managed generated tables**.

Implementation principle:
- CSV is uploaded
- schema is inferred
- admin reviews the inferred schema
- system creates or updates a controlled physical table for that dataset version
- metadata is stored in `datasets`, `dataset_versions`, `dataset_columns`

Suggested generated naming convention:
- `tenant_dataset_<dataset_id>_v<version_no>`

Only controlled application code may create these tables.

Never allow raw user-uploaded SQL or direct table creation from the UI.

---

## 17. FAQ Module

### 17.1 Purpose

Provide fixed, curated answers for frequent and high-confidence questions.

### 17.2 Why FAQ matters

FAQ answers should have **higher priority** than generated RAG answers where relevant.

Best use cases:
- form names
- escalation contacts
- recurring procedures
- fixed company policy answers
- customer service scripts

### 17.3 FAQ retrieval behavior

Search strategy:
- exact or near-exact semantic match
- optional keyword match
- priority-weighted ranking
- approved content only by default

### 17.4 FAQ admin features

- create FAQ
- edit FAQ
- approve FAQ
- archive FAQ
- tag FAQ
- set priority

---

## 18. Document Knowledge (RAG) Module

## 18.1 Purpose

Store and search PDF-based knowledge such as:
- SOPs
- manuals
- policies
- procedures
- emergency instructions
- compliance documents

## 18.2 Document pipeline

1. user uploads PDF
2. file stored in MinIO
3. ingestion job starts
4. text extracted
5. optional OCR path if needed later
6. text segmented into chunks
7. embeddings generated via Ollama-supported local model
8. chunks stored in `document_chunks`
9. document becomes searchable

## 18.3 Chunking guidelines

Recommended chunking targets:
- preserve section headings
- chunk by semantic or structured boundaries when possible
- target chunk size around 300–800 tokens
- overlap 50–120 tokens depending on doc type

## 18.4 Required metadata per chunk

- `company_id`
- `document_id`
- `page_no`
- `section_title`
- `chunk_index`
- `token_count`
- `embedding`

## 18.5 Retrieval strategy

Use hybrid document retrieval:
- vector similarity
- optional keyword or full text search
- filter by `company_id`
- filter by `status = approved` by default for sensitive domains

---

## 19. CSV Ingestion Module

## 19.1 Purpose

Allow Super Admin to upload company data from CSV files and make it available for natural-language querying.

## 19.2 CSV ingestion flow

```text
Upload CSV
  -> store raw file in MinIO
  -> create import job
  -> parse headers
  -> infer schema
  -> preview rows
  -> normalize column names
  -> allow admin confirmation
  -> create/update managed table
  -> insert rows
  -> store metadata
  -> mark dataset version active
```

## 19.3 Required CSV features

- encoding detection
- delimiter detection
- header normalization
- type inference
- preview first N rows
- row-level error report
- append vs replace mode
- versioning

## 19.4 Column normalization

Example rules:
- lowercase
- replace spaces with underscores
- strip special characters
- avoid SQL reserved words
- store original name separately in metadata

---

## 20. Hybrid Question Answering Design

This is the most important runtime behavior.

## 20.1 Principle

The user should ask one question naturally.

The system internally decides how to gather evidence from:
- FAQ
- document RAG
- structured data

The user does not choose the source type.

## 20.2 Default hybrid pipeline

For most user questions, the system should do these in parallel:
1. FAQ retrieval
2. document retrieval
3. structured-data intent detection / planning

## 20.3 Why not always execute SQL

The system should **always consider** structured data, but should **not always execute SQL**.

Examples:
- "What is the procedure for emergency landing?" → likely FAQ + RAG only
- "How many incident reports were filed this month?" → structured data + maybe policy context
- "Which form should I use and how many are still pending?" → hybrid with both

## 20.4 Hybrid orchestrator flow

```text
User question
  -> identify tenant/user/role
  -> FAQ retrieval
  -> document retrieval
  -> structured-data planner
     -> decide whether SQL is needed
     -> identify likely dataset/table
     -> generate safe SQL if needed
     -> execute SQL with limits
  -> merge evidence
  -> rerank evidence
  -> build grounded prompt
  -> local LLM synthesizes answer
  -> store answer, citations, and logs
```

## 20.5 Evidence priority

Recommended ranking order:
1. approved FAQ
2. approved SOP/manual chunks
3. structured data results
4. secondary document evidence

This reduces hallucination and keeps important answers controlled.

---

## 21. Structured Data Planner and Safe SQL

## 21.1 Purpose

Determine whether a question needs structured data and safely answer it.

## 21.2 Planner responsibilities

- detect whether the question likely needs tables
- choose candidate dataset(s)
- provide schema context to the model
- generate safe read-only SQL
- validate SQL before execution
- execute with limits
- convert results into compact evidence for final answer

## 21.3 Schema context provided to LLM

Only provide:
- table name
- table description
- columns
- types
- maybe small redacted examples if needed

Avoid sending raw sensitive rows unless absolutely necessary.

## 21.4 SQL safety rules

Mandatory rules:
- SELECT only
- no INSERT/UPDATE/DELETE/ALTER/DROP/TRUNCATE
- no multiple statements
- no unsafe functions
- row limit enforced
- timeout enforced
- allowlist dataset tables only
- tenant scoping required

## 21.5 SQL validation steps

1. parse/inspect generated SQL
2. reject if not SELECT
3. reject if references non-allowlisted tables
4. ensure tenant scope exists where relevant
5. inject or validate `LIMIT`
6. run with timeout
7. log execution

## 21.6 SQL execution output

Convert SQL result to compact evidence, for example:
- summary sentence
- first few relevant rows
- total count
- date range

The final LLM answer should not rely on raw SQL tables alone without a readable summarization layer.

---

## 22. LLM Provider Design

## 22.1 Requirement

Use **local/self-hosted LLM only**.

The architecture must not depend on external paid model APIs.

## 22.2 Provider abstraction

Recommended interface:

```python
class LLMProvider(Protocol):
    def chat(self, messages: list[dict], model: str, temperature: float = 0.0) -> str: ...
    def embed(self, texts: list[str], model: str) -> list[list[float]]: ...
```

## 22.3 Initial provider

Implement `OllamaProvider` with support for:
- chat generation
- embedding generation

## 22.4 Future extensibility

Later optional providers:
- vLLM provider
- llama.cpp provider

Backend business logic should call the abstraction, not Ollama directly.

---

## 23. Prompting Strategy

## 23.1 Final answer prompt

The answer-generation prompt should:
- clearly state the user question
- provide tenant-safe evidence only
- instruct the model to answer only from evidence
- instruct it to say when evidence is insufficient
- include citation references
- include role-based constraints if needed

## 23.2 High-risk domains

For domains like emergency procedures or compliance:
- answer only from approved documents or curated FAQ
- prefer document version metadata
- include escalation note if evidence is incomplete
- avoid speculative language

## 23.3 Model behavior rules

The model should be instructed to:
- not invent policies
- not invent data counts
- not claim certainty without evidence
- not use unsupported assumptions

---

## 24. Chat Module Design

## 24.1 Chat session behavior

- user can create multiple chat sessions
- each message belongs to one session
- session title can be auto-generated from first message

## 24.2 Message storage

Store:
- raw user message
- final assistant message
- selected sources
- model used
- timestamps

## 24.3 Optional conversation memory

For v1, keep limited short-term session context. Do not implement overly complex long-term memory inside the tenant assistant yet.

Recommended:
- last N chat turns included in answer prompt
- older history summarized later if needed

---

## 25. Admin Module Design

## 25.1 Company management

Super Admin can:
- create company
- edit company profile
- activate/deactivate company

## 25.2 User management

Super Admin can:
- create user
- assign company
- reset password
- activate/deactivate user

## 25.3 Knowledge management

Super Admin can:
- upload PDF
- upload CSV
- create FAQ
- approve/archive content
- review ingestion history

## 25.4 Review and audit

Super Admin can:
- inspect answer sources
- inspect SQL query logs
- review failed imports
- view user feedback

---

## 26. API Design

Below is the recommended initial API surface.

## 26.1 Auth

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

## 26.2 Companies

- `GET /api/companies`
- `POST /api/companies`
- `GET /api/companies/{company_id}`
- `PATCH /api/companies/{company_id}`

## 26.3 Users

- `GET /api/users`
- `POST /api/users`
- `GET /api/users/{user_id}`
- `PATCH /api/users/{user_id}`
- `POST /api/users/{user_id}/reset-password`

## 26.4 FAQ

- `GET /api/faqs`
- `POST /api/faqs`
- `GET /api/faqs/{faq_id}`
- `PATCH /api/faqs/{faq_id}`
- `DELETE /api/faqs/{faq_id}` or archive endpoint

## 26.5 Documents

- `GET /api/documents`
- `POST /api/documents/upload`
- `GET /api/documents/{document_id}`
- `PATCH /api/documents/{document_id}`
- `POST /api/documents/{document_id}/reindex`
- `POST /api/documents/{document_id}/approve`
- `POST /api/documents/{document_id}/archive`

## 26.6 Datasets

- `GET /api/datasets`
- `POST /api/datasets/upload`
- `GET /api/datasets/{dataset_id}`
- `GET /api/datasets/{dataset_id}/versions`
- `GET /api/datasets/{dataset_id}/preview`
- `POST /api/datasets/{dataset_id}/import`
- `POST /api/datasets/{dataset_id}/activate-version`

## 26.7 Chat

- `GET /api/chat/sessions`
- `POST /api/chat/sessions`
- `GET /api/chat/sessions/{session_id}`
- `POST /api/chat/sessions/{session_id}/messages`
- `GET /api/chat/sessions/{session_id}/messages`

## 26.8 Audit and feedback

- `GET /api/audit/logs`
- `GET /api/sql/logs`
- `POST /api/messages/{message_id}/feedback`

---

## 27. Frontend Screen Requirements

## 27.1 Login page
- email/password login
- forgot/reset password optional later

## 27.2 User chat dashboard
- chat sidebar
- message area
- input box
- citations panel
- feedback actions

## 27.3 Admin dashboard
- company list
- user management
- knowledge stats
- recent imports
- recent questions

## 27.4 FAQ management page
- create/edit/archive FAQ
- status filter
- category filter

## 27.5 Document management page
- upload PDF
- view status
- reindex
- approve/archive
- preview metadata

## 27.6 Dataset management page
- upload CSV
- schema preview
- import history
- version list
- errors preview

## 27.7 Audit pages
- answer source logs
- SQL logs
- user feedback
- failed job list

---

## 28. Background Job Design

## 28.1 Job types
- PDF parse/index
- CSV parse/import
- reindex document
- backfill embeddings
- cleanup temporary artifacts

## 28.2 Job states
- pending
- running
- completed
- failed

## 28.3 Retry strategy
- retry transient failures only
- do not infinitely retry malformed files
- capture detailed error message in `import_jobs`

---

## 29. File Storage Design

## 29.1 MinIO usage

MinIO will store original uploaded files.

Objects may include:
- raw CSV files
- raw PDF files
- optional extracted text JSON
- optional OCR output later

## 29.2 Object naming convention

Suggested pattern:

```text
companies/{company_id}/documents/{document_id}/{filename}
companies/{company_id}/datasets/{dataset_id}/versions/{version_id}/{filename}
```

## 29.3 Required metadata

Store metadata in PostgreSQL, not only inside object store.

Required metadata:
- object key
- original filename
- uploaded by
- upload time
- mime type
- size

---

## 30. Mac mini File Path Recommendations

Suggested local path layout:

```text
/Users/<your_user>/ai-platform/
├─ app/
├─ data/
│  ├─ postgres/
│  ├─ minio/
│  ├─ ollama/
│  ├─ backups/
│  └─ logs/
├─ infra/
│  ├─ caddy/
│  ├─ cloudflared/
│  └─ system/
└─ scripts/
```

If using an external drive, ensure stable mount path and backup strategy.

---

## 31. Process Management

## 31.1 On Mac mini

Possible options:
- run services manually during development
- use `brew services` where supported
- use `pm2` or native process supervision for app processes if needed
- keep infrastructure services installed natively

Recommended practical split:
- PostgreSQL via package manager/service
- Redis via package manager/service
- MinIO as native binary/service
- Ollama native install
- Next.js and FastAPI managed by a simple process manager during initial deployment
- `cloudflared` native install/service

## 31.2 On future Linux VPS

Use `systemd` unit files for:
- frontend
- backend
- worker
- MinIO
- Ollama if self-hosted there
- cloudflared if tunnel retained

---

## 32. Security Controls

## 32.1 Mandatory controls
- auth required for all internal endpoints except login/health where appropriate
- tenant scoping on every data access
- role checks on admin endpoints
- file type validation on upload
- size limits for uploads
- SQL safety validation
- structured audit logging

## 32.2 Upload security
- validate allowed MIME types
- reject executable files
- optionally scan files for malware later

## 32.3 Prompt injection defense

Documents must be treated as untrusted content.

Rules:
- retrieved document text is evidence, not instruction
- system prompt must override any malicious document text
- never allow a document to redefine developer/system rules

## 32.4 Sensitive data handling
- avoid sending raw private row samples unless necessary
- limit stored chat history exposure to authorized users only
- redact error details from end-user messages where appropriate

---

## 33. Audit and Logging

## 33.1 Must-log events
- login
- logout
- company creation
- user creation and update
- FAQ creation/update/archive
- document upload/index/approve/archive
- CSV upload/import/activate
- chat question submitted
- answer generated
- SQL query executed
- feedback submitted

## 33.2 Log fields
- actor user id
- company id
- event type
- target entity
- timestamp
- metadata JSON

## 33.3 SQL log requirements
- original question
- generated SQL
- final executed SQL
- row count
- latency
- error if failed

---

## 34. Backup and Recovery

## 34.1 What must be backed up
- PostgreSQL database
- MinIO files
- environment files
- reverse proxy config
- cloudflared config
- app secrets securely stored
- model configuration list

## 34.2 Backup schedule

Recommended minimum:
- daily DB backup
- daily or frequent MinIO sync/backup
- weekly full restore test in non-production environment

## 34.3 Recovery objective

Be able to restore to:
- another Mac
- Linux VPS
- fresh machine after hardware failure

---

## 35. Testing Strategy

## 35.1 Unit tests
- auth utils
- SQL safety validator
- tenant filter helpers
- FAQ retriever
- chunking logic
- import parser

## 35.2 Integration tests
- login flow
- PDF upload and index flow
- CSV import flow
- chat flow with FAQ only
- chat flow with RAG only
- chat flow with SQL only
- hybrid chat flow
- cross-tenant isolation tests

## 35.3 End-to-end tests
- admin uploads document
- admin uploads dataset
- user asks question
- user receives grounded answer with source

## 35.4 Critical security tests
- user from Company A cannot access Company B content
- SQL validator rejects disallowed queries
- archived content not retrieved unless explicitly allowed

---

## 36. Performance and Scaling Notes

## 36.1 Early-stage expectation

Mac mini should handle:
- light to moderate internal traffic
- small company usage
- local model inference for practical prototype/early production

## 36.2 Likely bottlenecks
- embedding generation on large document batches
- local LLM inference latency
- complex SQL queries on badly designed imported tables

## 36.3 Scaling path

Later options:
- move to Linux VPS
- separate LLM host from app host
- use stronger local model server
- split worker from main API host
- move MinIO to managed object storage later if desired

---

## 37. Development Phases

## Phase 1 — Foundation
- repo setup
- auth
- companies and users
- tenant-aware DB models
- Next.js basic UI shell
- FastAPI basic API

## Phase 2 — Knowledge Management
- FAQ CRUD
- PDF upload
- MinIO integration
- document parsing/chunking/indexing
- document retrieval

## Phase 3 — Structured Data
- CSV upload
- schema inference
- managed table generation
- SQL planner and validator
- structured data answering

## Phase 4 — Hybrid Chat
- chat sessions/messages
- orchestrator
- evidence merger
- answer generation
- citations and logs

## Phase 5 — Hardening
- feedback
- admin audit screens
- backup scripts
- production configs
- migration runbook to VPS

---

## 38. Acceptance Criteria

The system will be considered ready for first real deployment when it can do all of the following:

1. Super Admin can create a company and user.
2. Super Admin can upload a PDF and it becomes searchable.
3. Super Admin can upload a CSV and it becomes queryable.
4. Standard User can log in and ask natural-language questions.
5. The system automatically decides whether to use FAQ, RAG, SQL, or hybrid.
6. Answers include evidence references where applicable.
7. A user cannot access another company’s data.
8. Dangerous SQL is blocked.
9. Uploads and chat actions are logged.
10. The system can be backed up and restored.

---

## 39. Recommended Initial Build Decisions

To avoid overengineering, use these defaults first:

- 2 roles only
- one shared PostgreSQL database
- row-level tenant isolation
- one local Ollama provider
- one embedding model
- approved FAQ prioritized above all else
- approved documents prioritized above general documents
- SQL executed only when planner says it is needed
- Cloudflare Tunnel for public exposure
- MinIO on local disk
- no Docker

---

## 40. Final Implementation Principle

Build the product so that the end user experiences a simple assistant, while the internal system behaves like a governed multi-source evidence engine.

The user asks one question.
The system privately decides where to search.
The answer is grounded, tenant-safe, auditable, and practical for real company use.

