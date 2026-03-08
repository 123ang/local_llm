# Production Multi-Tenant Customer Service Platform Blueprint

## 1. Product Goal
Build a **multi-user, multi-company customer-service knowledge platform** where:
- A **platform admin** can create companies (tenants)
- Each company gets its own isolated data space
- Company admins can upload **CSV files** to create/update tables
- Company admins can upload **PDFs / SOPs / manuals / policies / emergency procedures** to build a knowledge base
- Normal users can log in and ask questions in natural language
- The system answers using:
  - structured database data
  - PDF knowledge base (RAG)
  - FAQ / workflow guidance
- The platform can serve use cases like **airport operations**, **SME customer service**, **internal SOP assistant**, **incident response**, and **compliance guidance**

---

## 2. Recommended Product Positioning
This should be designed as a **B2B multi-tenant SaaS platform**.

### Core value
Each company can turn its own:
- spreadsheets
- SOP documents
- policies
- forms
- internal manuals

into a searchable AI assistant for staff or customer support.

### Example use cases
- Airport staff assistant: "What should I do if an aircraft incident happens on the runway?"
- Retail support assistant: "How do I process a refund over RM500?"
- HR assistant: "Which form is needed for unpaid leave?"
- Finance assistant: "Which report section includes overdue invoices?"
- Operations assistant: "What is the escalation path for a fire incident?"

---

## 3. High-Level Recommendation
For production, **do NOT create one physical database server per company at the start** unless the tenant is very large or highly regulated.

### Recommended tenancy model for v1 production
Use:
- **One PostgreSQL cluster**
- **Shared application database** for platform data
- **Tenant isolation by `company_id`** for application/business records
- **Separate object storage paths per company** for raw files
- **Separate vector collections / namespaces per company** for retrieval

### Why this is better than “one database per company” initially
Pros:
- easier to maintain
- cheaper
- easier backups / migrations / monitoring
- simpler deployment
- easier onboarding

### When to move to dedicated DB per company
Only later when a company needs:
- very large volume
- strict compliance isolation
- enterprise contract requirement
- custom retention or region rules

### Best approach
Design the software in a way that supports **future upgrade** from:
- shared DB multi-tenant
- to dedicated DB / schema per enterprise tenant

This is called a **hybrid tenancy architecture**.

---

## 4. Recommended Tech Stack

## Frontend
- **Next.js** (App Router)
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Charting: Recharts

## Backend API
- **FastAPI**
- Pydantic
- SQLAlchemy / SQLModel
- background jobs via native worker process
- Redis for queue + caching

## Database\([fastapi.tiangolo.com](https://fastapi.tiangolo.com/deployment/concepts/?utm_source=chatgpt.com))age
- S3-compatible storage
  - home deployment: **MinIO** using local disk paths
  - VPS deployment: MinIO on local disk, or later a managed object store if desired

## Authentication
- local auth with JWT / session cookies
- optional future SSO later

## AI / LLM Layer
- **local/self-hosted only**
- provider abstraction for:
  - Ollama
  - vLLM
  - llama.cpp-style local inference servers
- separate embedding service abstraction for local embedding models

## Search / Retrieval
- pgvector in PostgreSQL
- hybrid retrieval:
  - vector similarity
  - Postgres full text / keyword matching

## Reverse Proxy / Edge
- internal reverse proxy: **Caddy** or **Nginx**
- public exposure for home deployment: **Cloudflare Tunnel**
- optional private admin access: **Tailscale**

## Process Management
- **systemd** on Linux VPS
- on Mac mini: launch services directly during development, or keep app processes supervised through a lightweight process manager until migration to Linux VPS

## Observability
- OpenTelemetry
- Prometheus + Grafana later
- Sentry or self-hosted error tracking
- structured logs

## Deployment model
- **native deployment without Docker**
- home server target: **Mac mini**
- migration target: **Linux VPS** with the same app structure and environment variables

---

## 5. Main Product Modules

### A. Platform Administration Module
Used by system owner / super admin.

Functions:
- create company
- suspend company
- set subscription plan
- assign company admin
- configure storage quota
- configure model access
- view usage and logs

### B. Company Administration Module
Used by each tenant admin.

Functions:
- manage users
- create departments / teams
- upload CSV
- map CSV columns
- create/update tables
- upload PDFs
- tag documents
- manage FAQ articles
- manage answer rules / guardrails
- configure visible data sources
- review chat logs

### C. Data Ingestion Module
Functions:
- upload CSV
- validate file format
- infer schema
- map columns
- create/import table
- version imported data
- schedule re-imports later

### D. Document Knowledge Module
Functions:
- upload PDF / DOCX later
- OCR if needed
- parse structure
- chunk text
- embed chunks
- store in pgvector
- attach metadata:
  - company_id
  - document type
  - title
  - version
  - department
  - tags
  - effective date

### E. Chat / AI Assistant Module
Functions:
- user chat
- source routing
- retrieve relevant chunks
- optionally query structured data
- produce grounded answer
- cite sources
- store conversation history
- apply role restrictions

### F. FAQ / Workflow Module
Functions:
- store curated Q&A
- store pre-approved SOP steps
- pin critical answers
- prioritize verified content over model-generated answers

### G. Audit / Governance Module
Functions:
- track uploads
- track who changed knowledge
- log queries
- log model outputs
- flag risky answers
- allow review workflow

---

## 6. Users and Roles

### 1. Super Admin
Single high-privilege operator for the platform and each tenant.
This role combines:
- platform administration
- company administration
- knowledge editing
- auditing

Can:
- create companies
- manage tenant settings
- invite/manage users
- upload/update CSV
- upload/update PDFs
- manage FAQ items
- review chat logs
- review answer quality
- audit usage and source history
- suspend or archive tenant content

### 2. Standard User
Can:
- log in
- ask questions
- receive grounded answers
- view citations / linked source documents
- submit feedback on answer quality

> Note: There is no separate company admin, auditor, or knowledge editor role in v1. Those responsibilities are handled by the Super Admin.

---

## 7. Core Architecture

```text
[Web / Mobile UI]
        |
        v
 [API Gateway / Backend]
        |
        +------------------------------+
        |                              |
        v                              v
 [Auth & RBAC]                  [Chat Orchestrator]
                                       |
                  +--------------------+--------------------+
                  |                    |                    |
                  v                    v                    v
           [FAQ Service]      [Structured Data Service]  [RAG Service]
                  |                    |                    |
                  v                    v                    v
         [FAQ Tables / Rules]   [Tenant Tables in PG]   [pgvector + docs]

                  +------------------------------------------+
                  |
                  v
           [Audit Logs / Analytics]
```

---

## 8. Recommended Data Isolation Strategy

## Option A: Shared DB, row-level tenant isolation
All app data in one PostgreSQL database.
Every relevant table includes `company_id`.

Examples:
- companies
- users
- documents
- document_chunks
- faq_items
- chat_sessions
- chat_messages
- import_jobs
- audit_logs

Business data imported from CSV also includes `company_id`.

### Pros
- simplest operations
- easiest onboarding
- lowest infra cost

### Cons
- requires strict tenant filtering everywhere
- higher risk if code has isolation bug

## Option B: Shared DB + separate schema per company
Example:
- platform tables in `public`
- company A business tables in `tenant_a`
- company B business tables in `tenant_b`

### Pros
- cleaner separation
- easier backup/export per company

### Cons
- migration complexity grows with tenants

## Option C: Dedicated DB per company
### Pros
- strongest isolation
- enterprise-friendly

### Cons
- operationally expensive
- more complex to manage

## Recommendation
For your use case:
- **v1 production:** Option A or A + light namespace strategy
- **v2 enterprise:** support Option C for special tenants

---

## 9. Authentication and Access Control

### Authentication
Use:
- email/password + MFA
- optional Google/Microsoft SSO later

### Authorization
Use RBAC + tenant scoping.
Every request should carry:
- `user_id`
- `company_id`
- `role`

The backend must enforce:
- user belongs to company
- source belongs to company
- requested action allowed for role

### Important production rule
Never rely on frontend role headers alone.
Everything must be checked server-side.

---

## 10. Ingestion Flow for CSV

```text
Company Admin uploads CSV
        |
        v
File stored in object storage
        |
        v
Ingestion job validates file
        |
        v
Schema inference + preview
        |
        v
Admin confirms mapping
        |
        v
System creates/imports tenant table
        |
        v
Metadata stored in import history
        |
        v
Table becomes available to AI query layer
```

### CSV ingestion capabilities
- delimiter detection
- encoding detection
- preview 50 rows
- map columns manually
- type inference:
  - text
  - integer
  - decimal
  - date
  - boolean
- reject malformed rows into error report
- create versioned import
- soft replace or append mode

### Recommendation
Do not let uploaded CSV create arbitrary SQL tables directly without review.
Use a controlled import pipeline.

---

## 11. Ingestion Flow for PDF / Knowledge Files

```text
Company Admin uploads PDF
        |
        v
Store raw file in object storage
        |
        v
Parse text / OCR if needed
        |
        v
Split into chunks
        |
        v
Generate embeddings
        |
        v
Store chunks + metadata in pgvector
        |
        v
Mark document as indexed and searchable
```

### Metadata to store per document
- company_id
- document_id
- title
- filename
- department
- category
- effective_date
- version
- uploaded_by
- visibility level
- status: draft / approved / archived

### Metadata to store per chunk
- chunk_id
- document_id
- company_id
- page number
- section heading
- chunk text
- embedding
- token count

---

## 12. Chat Query Flow

```text
User asks question
        |
        v
Authenticate user
        |
        v
Resolve tenant context from session
  - user_id
  - company_id
  - role
        |
        v
Hybrid retrieval runs by default
  - FAQ / approved answer lookup
  - RAG retrieval over PDF knowledge
  - structured data planning/query
        |
        v
Normalize all candidate evidence into one result set
        |
        v
Rerank and prioritize sources
  1. approved FAQ / curated answer
  2. approved SOP / policy chunks
  3. structured data result
  4. secondary document evidence
        |
        v
LLM synthesizes one grounded answer
        |
        v
Return answer + citations + escalation note if needed
        |
        v
Log query, sources, SQL used, and answer for audit
```

### Important design choice
Users should **not need to know** whether information is stored in:
- FAQ
- PDF / RAG knowledge
- structured tables

The system should search across all relevant tenant sources automatically.

### Recommended default behavior
For most user queries, run these in parallel:
- FAQ search
- vector + keyword document retrieval
- structured-data planner

Then combine and rerank results before answer generation.

### Structured-data planner behavior
The structured-data planner should first decide whether the question is likely answerable from tenant tables.
If yes:
- identify candidate tables from metadata / data dictionary
- generate safe read-only SQL
- execute with row/time/result limits
- convert results into compact evidence for the final answer

If not:
- skip SQL execution and rely on FAQ/RAG only

### Why this is the best UX
The user only asks one question.
The system handles the storage differences internally.
That creates a much more natural customer-service experience.

---

## 13. Recommended Answering Strategy

Use **priority-based grounding**:

1. Curated FAQ / approved answer
2. Approved SOP / policy chunks
3. Structured data result
4. General model reasoning only when grounded sources are insufficient

### Critical rule
For high-risk domains like airport incidents, safety, compliance, HR, legal, or emergency response:
- prefer approved documents
- show citation and document version
- avoid speculative answers
- add escalation note when confidence is low

Example:
> "Based on Emergency Response Manual v3.2, Section 4.1, notify Airport Fire & Rescue Service immediately and initiate incident reporting Form IR-02. Please verify with duty supervisor if the incident involves fuel leakage."

---

## 14. Production Data Model (Core Tables)

## Platform tables
- companies
- company_settings
- users
- memberships
- roles
- api_keys (optional)
- subscriptions

## Knowledge tables
- documents
- document_versions
- document_chunks
- faq_items
- faq_categories
- knowledge_tags

## Chat tables
- chat_sessions
- chat_messages
- answer_sources
- feedback

## Import tables
- datasets
- dataset_versions
- dataset_tables
- import_jobs
- import_errors
- data_dictionary

## Governance tables
- audit_logs
- access_logs
- policy_rules
- review_tasks

---

## 15. Key Security Requirements

### Must-have
- tenant isolation enforced in backend
- encrypted passwords / secure auth provider
- HTTPS everywhere
- signed file upload URLs or controlled upload endpoints
- object storage access restrictions
- audit logs
- row-level access restrictions if needed
- database least privilege
- prompt injection defense in retrieval pipeline
- file virus scanning if public uploads are possible

### For SQL generation
If users can ask questions over imported tables:
- read-only DB role
- allowlist accessible tables
- allowlist columns if needed
- SQL parser validation
- query timeout
- row limit
- no DDL / no DML
- no dangerous functions
- result size cap

---

## 16. Important Product Safety Layer
For your airport example, this is extremely important.

The system should support **answer classes**:
- informational
- operational
- critical safety
- regulated / compliance

For critical safety questions:
- show prominent warning banner
- cite exact source
- show document effective date
- require approved source only
- optionally block answering if no approved source exists
- suggest escalation contact

Example:
- “What to do during aircraft crash?” should not be answered from general AI reasoning alone.
- It must use approved emergency manuals and response SOPs.

---

## 17. Suggested Product Screens

### Super Admin
- company list
- create company
- tenant health dashboard
- subscription / quota page

### Company Admin
- dashboard
- user management
- upload center
- datasets
- documents
- FAQ manager
- approvals
- audit logs
- model settings

### Standard User
- chat interface
- source citations panel
- saved conversations
- FAQ browser
- feedback button

### Reviewer
- answer review queue
- low-confidence answer queue
- outdated document alerts

---

## 18. Suggested System Flow for Admin Onboarding

```text
Super Admin creates company
        |
        v
System provisions tenant record + default settings
        |
        v
Company Admin invited by email
        |
        v
Company Admin logs in
        |
        v
Uploads first CSV + PDFs
        |
        v
System indexes knowledge
        |
        v
Company Admin reviews FAQ / permissions
        |
        v
Users start asking questions
```

---

## 19. Recommended Development Phases

## Phase 1 — Foundation
- auth
- multi-tenant RBAC
- company creation
- file storage
- document upload
- PDF chunking + embeddings
- chat with RAG

## Phase 2 — Structured Data
- CSV upload
- schema mapping
- dataset versioning
- safe text-to-SQL
- hybrid answers

## Phase 3 — Governance
- FAQ approval workflow
- audit logs
- answer review
- confidence policies
- document lifecycle

## Phase 4 — Enterprise Features
- SSO
- API access
- dedicated tenant DB option
- advanced analytics
- multilingual support
- workflow integrations

---

## 20. Recommended Architecture Decision for Your Case

### Best v1 production architecture
- Next.js frontend
- FastAPI backend
- PostgreSQL + pgvector
- Redis for jobs/cache
- MinIO for file storage in home deployment
- native background worker for ingestion
- local-only model abstraction layer
- multi-tenant shared DB with row-level tenant isolation via `company_id`
- strict server-side role enforcement
- hybrid FAQ + RAG + structured-data answering by default
- Cloudflare Tunnel for public access from home network

### LLM strategy
The model layer should focus on **local/self-hosted models only**, such as:
- Ollama
- vLLM
- llama.cpp-based deployments
- other self-hosted local inference servers

Build an internal provider interface so you can swap models later without changing business logic.

### Why this fits your idea
It supports:
- many companies
- one powerful Super Admin workflow
- CSV + PDF ingestion
- FAQ customer service
- internal SOP / emergency procedure assistant
- automatic searching across both RAG and structured data without asking users to choose
- same architecture at home and on VPS with minimal code changes

---

## 21. Home Server and VPS Deployment Blueprint

## Core principle
Design the application so the **application structure is identical** in both places:
- home deployment on Mac mini
- future deployment on Linux VPS

Only the **edge/access layer**, startup method, and a few environment values should change.

## Recommended environments

### A. Home Production Environment (Mac mini)
Use for:
- first real deployment
- private/internal company usage
- controlled traffic volumes
- local model hosting

### B. VPS Production Environment
Use for:
- better uptime
- public internet access at scale
- simpler process supervision
- optional separation between app and model hosts later

---

## 22. Recommended exposure method: Tunnel vs direct public exposure

### Best default choice: Cloudflare Tunnel
For a Mac mini running on home internet, the best default production exposure method is:
- keep your app private on the home network
- run `cloudflared`
- point your domain/subdomain to Cloudflare
- let Cloudflare forward traffic to your internal reverse proxy

### Why this is the best choice
- no need to expose inbound ports on your router
- no dependency on a stable public IP
- easier if ISP changes your IP
- lower attack surface than direct port-forwarding
- simpler migration path because your public DNS stays the same when you move later to a VPS

### When to use Tailscale
Use Tailscale for:
- private admin access
- SSH access
- remote maintenance
- internal dashboards not meant for public users

### Recommended combination
- **Public app traffic**: Cloudflare Tunnel
- **Private admin/server access**: Tailscale

### What not to do for v1
Avoid direct router port-forwarding to your Mac mini unless absolutely necessary.
That is harder to secure and less portable.

---

## 23. Home Deployment Topology (Mac mini)

```text
[Users on Internet]
        |
        v
   [Cloudflare DNS]
        |
        v
 [Cloudflare Tunnel / cloudflared]
        |
        v
 [Caddy or Nginx reverse proxy]
        |
        +--------------------+--------------------+
        |                    |                    |
        v                    v                    v
   [Next.js UI]        [FastAPI API]      [Optional Admin Tools]
                              |
                              +--------------------+-------------------+------------------+
                              |                    |                   |                  |
                              v                    v                   v                  v
                        [PostgreSQL + pgvector] [Redis]        [Worker / Ingestion] [MinIO]
                              |
                              v
                      [Local LLM Service Layer]
                              |
                +-------------+-------------+
                |                           |
                v                           v
            [Ollama]                    [Embedding Model]
```

---

## 24. VPS Deployment Topology

```text
[Users on Internet]
        |
        v
   [Cloudflare DNS]
        |
        v
 [Caddy or Nginx on VPS]
        |
        +--------------------+--------------------+
        |                    |                    |
        v                    v                    v
   [Next.js UI]        [FastAPI API]       [Optional Admin Tools]
                              |
                              +--------------------+-------------------+------------------+
                              |                    |                   |                  |
                              v                    v                   v                  v
                        [PostgreSQL + pgvector] [Redis]        [Worker / Ingestion] [MinIO]
                              |
                              v
                      [Local LLM Service Layer]
                              |
                              v
                           [Ollama]
```

### Migration idea
Keep the same:
- repository structure
- environment variable names
- database schema
- storage bucket layout
- domain names

Then migration is mostly:
- copy code
- restore database backup
- restore MinIO files
- reconfigure system services
- switch Cloudflare origin to the VPS

---

## 25. Native service layout

### Core services
- `caddy` or `nginx` → reverse proxy
- `nextjs` → frontend app service
- `fastapi` → backend API service
- `worker` → background jobs / ingestion service
- `postgresql` → PostgreSQL with pgvector
- `redis` → job queue and cache
- `minio` → object storage
- `ollama` → local LLM inference
- `cloudflared` → public tunnel for home deployment only

### Optional services
- `pgadmin` or similar DB tool, restricted to private access
- `prometheus` / `grafana` for monitoring
- `fail2ban` or similar host hardening tools on VPS

### Startup model
On VPS, run the app processes as native services, typically with `systemd`, so they restart automatically on boot and after failure.

---

## 26. Codebase strategy for portability

Use one codebase with environment-based deployment.

### Shared application structure
- `frontend/` → Next.js app
- `backend/` → FastAPI app
- `worker/` → background job entrypoints
- `infra/` → config templates, service files, reverse proxy config
- `scripts/` → backup, restore, deployment scripts

### Home environment config
Use environment values for:
- local paths
- Cloudflare Tunnel target
- lower resource settings if needed
- local hostnames

### VPS environment config
Use environment values for:
- public reverse proxy config
- backup paths
- production resource settings
- hostnames

---

## 27. Domain and routing design

### Recommended domain layout
- `app.yourdomain.com` → main user app
- `api.yourdomain.com` → API if needed separately
- `admin.yourdomain.com` → optional future admin panel

### Home deployment routing
Domain points to Cloudflare.
Cloudflare routes traffic through Tunnel to the Mac mini.
The reverse proxy on the Mac mini routes requests to the right local service.

### VPS deployment routing
Domain still points to Cloudflare.
Cloudflare points directly to VPS reverse proxy, or continues through a tunnel if desired.

### Why this helps migration
Your public domain does not need to change when you move from home to VPS.
Only the origin changes.

---

## 28. Storage layout

### PostgreSQL
Stores:
- platform metadata
- tenant data
- FAQ
- document metadata
- vectors via pgvector
- audit logs

### MinIO
Stores:
- original uploaded CSV files
- original uploaded PDFs
- derived artifacts if needed
  - OCR text
  - extracted JSON
  - temporary ingestion exports

### Local disk paths
Persist these in stable paths:
- PostgreSQL data directory
- MinIO data directory
- Ollama model directory
- application logs
- backup directory

---

## 29. Recommended network model

### Internal service communication
All core services communicate on the local machine using localhost or private interfaces.
Expose only the reverse proxy internally to the tunnel.

### Public exposure
For home deployment:
- only `cloudflared` talks outward
- reverse proxy should not be directly exposed to the internet by router port-forwarding

### Admin access
Use Tailscale for:
- SSH to Mac mini or VPS
- private DB inspection
- internal admin tools
- emergency maintenance

---

## 30. Mac mini-specific design notes

### Why Mac mini works well for v1
- always-on local machine
- good efficiency for 24/7 usage
- suitable for light-to-moderate internal workloads
- good for local LLM experimentation and small production traffic

### Recommendation
Treat the Mac mini as:
- application host
- local model host
- initial production server

But design the stack so a Linux VPS can replace it later without rewriting the app.

---

## 31. Production operations plan

### Backups
At minimum back up:
- PostgreSQL dumps / base backups
- MinIO object storage
- environment files (securely)
- model configuration
- reverse proxy and tunnel config

### Restore testing
Regularly test restoring to another machine or VPS.
Portability only matters if restore really works.

### Logs
Centralize logs for:
- reverse proxy
- API
- worker
- cloudflared
- Ollama
- PostgreSQL if needed

### Health checks
Each service should expose health status where possible.
The reverse proxy should only route to healthy app services.

---

## 32. Recommended starting architecture for your exact case

### Home-first production
- Mac mini at home
- native services
- Cloudflare Tunnel for public access
- Tailscale for private admin access
- PostgreSQL + pgvector
- MinIO
- Redis
- FastAPI + Next.js
- Ollama local inference

### Future migration path
When traffic or reliability requirements increase:
1. move the same application code to a Linux VPS
2. restore Postgres + MinIO backups
3. point Cloudflare origin to VPS
4. optionally keep Mac mini as backup, staging, or model worker

---

## 33. Final infrastructure principle
Build once as a **portable platform**, not as a Mac-specific setup.

The Mac mini should be your first host.
Your repo and service configuration should be your deployment contract.
Cloudflare Tunnel should be your safest home-network edge.
A VPS should later be just another deployment target, not a redesign.

---

## 34. Final Product Principle Home Server and VPS Deployment Blueprint

## Core principle
Design the application so the **application stack is identical** in both places:
- home deployment on Mac mini
- future deployment on Linux VPS

Only the **edge/access layer** and a few environment values should change.

## Recommended environments

### A. Home Production Environment (Mac mini)
Use for:
- first real deployment
- private/internal company usage
- controlled traffic volumes
- local model hosting

### B. VPS Production Environment
Use for:
- better uptime
- public internet access at scale
- simpler networking
- optional separation between app and model hosts later

---

## 22. Recommended exposure method: Tunnel vs direct public exposure

### Best default choice: Cloudflare Tunnel
For a Mac mini running on home internet, the best default production exposure method is:
- keep your app private on the home network
- run `cloudflared` as a service/container
- point your domain/subdomain to Cloudflare
- let Cloudflare forward traffic to your internal reverse proxy

### Why this is the best choice
- no need to expose inbound ports on your router
- no dependency on a stable public IP
- easier if ISP changes your IP
- lower attack surface than direct port-forwarding
- simpler migration path because your public DNS stays the same when you move later to a VPS

### When to use Tailscale
Use Tailscale for:
- private admin access
- SSH access
- remote maintenance
- internal dashboards not meant for public users

### Recommended combination
- **Public app traffic**: Cloudflare Tunnel
- **Private admin/server access**: Tailscale

### What not to do for v1
Avoid direct router port-forwarding to your Mac mini unless absolutely necessary.
That is harder to secure and less portable.

---

## 23. Home Deployment Topology (Mac mini)

```text
[Users on Internet]
        |
        v
   [Cloudflare DNS]
        |
        v
 [Cloudflare Tunnel / cloudflared]
        |
        v
 [Traefik or Caddy reverse proxy]
        |
        +--------------------+--------------------+------------------+
        |                    |                    |                  |
        v                    v                    v                  v
   [Next.js UI]        [FastAPI API]      [MinIO Object Storage] [Optional Admin Tools]
                              |
                              +--------------------+-------------------+
                              |                    |                   |
                              v                    v                   v
                        [PostgreSQL + pgvector] [Redis]        [Worker / Ingestion]
                              |
                              v
                      [Local LLM Service Layer]
                              |
                +-------------+-------------+
                |                           |
                v                           v
            [Ollama]                    [Embedding Model]
```

---

## 24. VPS Deployment Topology

```text
[Users on Internet]
        |
        v
   [Cloudflare DNS]
        |
        v
 [Traefik or Caddy on VPS]
        |
        +--------------------+--------------------+------------------+
        |                    |                    |                  |
        v                    v                    v                  v
   [Next.js UI]        [FastAPI API]      [Object Storage]     [Admin Tools]
                              |
                              +--------------------+-------------------+
                              |                    |                   |
                              v                    v                   v
                        [PostgreSQL + pgvector] [Redis]        [Worker / Ingestion]
                              |
                              v
                      [Local LLM Service Layer]
                              |
                              v
                           [Ollama]
```

### Migration idea
Keep internal service names identical so migration is mostly:
- move Compose files
- move volumes / backups
- update environment variables
- switch off tunnel or keep it as needed

---

## 25. Docker-first service layout

### Core containers
- `proxy` → Traefik or Caddy
- `frontend` → Next.js app
- `api` → FastAPI app
- `worker` → background jobs / ingestion
- `postgres` → PostgreSQL with pgvector
- `redis` → job queue and cache
- `minio` → object storage
- `ollama` → local LLM inference
- `cloudflared` → public tunnel for home deployment only

### Optional containers
- `adminer` or `pgadmin` for DB inspection (disable publicly)
- `watchtower` only if you fully trust automated image updates
- `prometheus` / `grafana` for monitoring

---

## 26. Compose strategy for portability

Use multiple Compose files.

### Base file
`compose.yaml`
Contains services common to both Mac mini and VPS:
- frontend
- api
- worker
- postgres
- redis
- minio
- ollama
- internal networks
- named volumes

### Home override
`compose.home.yaml`
Adds:
- cloudflared
- home-specific volume paths
- lower resource settings if needed
- local DNS / local domain conveniences

### VPS override
`compose.vps.yaml`
Adds or changes:
- public reverse proxy settings
- backup agent
- production resource limits
- optional managed storage endpoints

### Example deployment commands
- Home: `docker compose -f compose.yaml -f compose.home.yaml up -d`
- VPS: `docker compose -f compose.yaml -f compose.vps.yaml up -d`

---

## 27. Domain and routing design

### Recommended domain layout
- `app.yourdomain.com` → main user app
- `api.yourdomain.com` → API if needed separately
- `admin.yourdomain.com` → optional future admin panel

### Home deployment routing
Domain points to Cloudflare.
Cloudflare routes traffic through Tunnel to the Mac mini.
The reverse proxy on the Mac mini routes requests to the right container.

### VPS deployment routing
Domain still points to Cloudflare.
Cloudflare points directly to VPS reverse proxy, or continues through a tunnel if desired.

### Why this helps migration
Your public domain does not need to change when you move from home to VPS.
Only the origin changes.

---

## 28. Storage layout

### PostgreSQL
Stores:
- platform metadata
- tenant data
- FAQ
- document metadata
- vectors via pgvector
- audit logs

### MinIO
Stores:
- original uploaded CSV files
- original uploaded PDFs
- derived artifacts if needed
  - OCR text
  - extracted JSON
  - temporary ingestion exports

### Local volumes
Persist these separately:
- `postgres_data`
- `minio_data`
- `ollama_data`
- optional app upload cache

---

## 29. Recommended network model

### Internal Docker network
All core services communicate over one internal private Docker network.
Expose only the reverse proxy internally to the tunnel.

### Public exposure
For home deployment:
- only `cloudflared` talks outward
- reverse proxy should not be directly exposed to the internet by router port-forwarding

### Admin access
Use Tailscale for:
- SSH to Mac mini
- private DB inspection
- internal admin tools
- emergency maintenance

---

## 30. Mac mini-specific design notes

### Why Mac mini works well for v1
- always-on local machine
- good efficiency for 24/7 usage
- suitable for light-to-moderate internal workloads
- good for local LLM experimentation and small production traffic

### Important platform note
On macOS, Docker runs through a Linux VM abstraction rather than native Linux behavior.
So keep deployment simple and avoid Linux-only networking assumptions.

### Recommendation
Treat the Mac mini as:
- application host
- local model host
- initial production server

But design the stack so a Linux VPS can replace it later without rewriting the app.

---

## 31. Production operations plan

### Backups
At minimum back up:
- PostgreSQL dumps / base backups
- MinIO object storage
- environment files (securely)
- model configuration

### Restore testing
Regularly test restoring to another machine or VPS.
Portability only matters if restore really works.

### Logs
Centralize logs for:
- proxy
- API
- worker
- cloudflared
- Ollama

### Health checks
Each container should expose health status.
The reverse proxy should only route to healthy services.

---

## 32. Recommended starting architecture for your exact case

### Home-first production
- Mac mini at home
- Docker Compose stack
- Cloudflare Tunnel for public access
- Tailscale for private admin access
- PostgreSQL + pgvector
- MinIO
- Redis
- FastAPI + Next.js
- Ollama local inference

### Future migration path
When traffic or reliability requirements increase:
1. move the same Compose stack to a Linux VPS
2. restore Postgres + MinIO backups
3. point Cloudflare origin to VPS
4. optionally keep Mac mini as backup, staging, or model worker

---

## 33. Final infrastructure principle
Build once as a **portable Docker platform**, not as a Mac-specific setup.

The Mac mini should be your first host.
Docker Compose should be your deployment contract.
Cloudflare Tunnel should be your safest home-network edge.
A VPS should later be just another deployment target, not a redesign.

---

## 34. Final Product Principle Final Product Principle
This should not be built as “a chatbot that reads files.”

It should be built as a **tenant-safe knowledge operations platform** with:
- controlled onboarding
- governed knowledge
- approved answers
- auditability
- flexible data sources
- production-grade access control

That positioning will make it much stronger for real business use.

