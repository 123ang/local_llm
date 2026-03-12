# AI Knowledge Platform — To-Do List and File Organization

## 1. Development To-Do List

### Phase 1 — Project Foundation
- decide final product name
- create monorepo
- set up frontend app
- set up backend app
- set up database
- set up local Ollama connection
- set up environment files
- define company/user/auth model
- define row-level company isolation rule

### Phase 2 — Authentication and Company Management
- build login/logout
- build session handling
- create Super Admin role
- create company
- create user under company
- list companies
- list users by company
- activate/deactivate user
- activate/deactivate company

### Phase 3 — Knowledge Management
- upload PDF
- store file metadata
- parse PDF text
- chunk documents
- generate embeddings
- save embeddings/vector references
- add FAQ item
- edit FAQ item
- publish/unpublish FAQ item
- link FAQ to company
- tag documents by category

### Phase 4 — Structured Data
- upload CSV
- preview CSV
- infer schema
- map fields
- import to database
- save dataset metadata
- list datasets by company
- version dataset imports
- validate SQL-safe tables

### Phase 5 — Chat Assistant
- build chat UI
- build chat history
- build conversation storage
- implement FAQ retrieval
- implement RAG retrieval
- implement structured data planner
- merge evidence
- call LLM
- save answer with sources
- support follow-up questions

### Phase 6 — Admin Controls
- review uploaded files
- review FAQ items
- review logs
- review failed imports
- review chat history
- flag low-confidence answers
- archive outdated knowledge

### Phase 7 — Security and Quality
- enforce `company_id` in every query
- read-only SQL generation rules
- file upload validation
- size limits
- logging and audit trail
- error handling
- backup strategy
- role checks in backend only

### Phase 8 — Deployment
- set up Mac mini services
- set up PostgreSQL
- set up MinIO or local file storage
- set up Ollama models
- set up reverse proxy
- set up Cloudflare Tunnel
- set up system service / launch scripts
- test restart and recovery
- test backup and restore

---

## 2. Recommended File Organization

```text
ai-knowledge-platform/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── login/
│   │   │   ├── dashboard/
│   │   │   ├── assistant/
│   │   │   ├── knowledge-base/
│   │   │   ├── companies/
│   │   │   ├── users/
│   │   │   ├── datasets/
│   │   │   ├── audit/
│   │   │   └── settings/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── chat/
│   │   │   ├── knowledge/
│   │   │   ├── forms/
│   │   │   └── tables/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   ├── constants.ts
│   │   │   └── utils.ts
│   │   ├── hooks/
│   │   ├── types/
│   │   └── styles/
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   ├── logger.py
│   │   │   └── dependencies.py
│   │   ├── models/
│   │   │   ├── company.py
│   │   │   ├── user.py
│   │   │   ├── faq.py
│   │   │   ├── document.py
│   │   │   ├── dataset.py
│   │   │   ├── chat.py
│   │   │   └── audit.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── company.py
│   │   │   ├── user.py
│   │   │   ├── faq.py
│   │   │   ├── document.py
│   │   │   ├── dataset.py
│   │   │   ├── chat.py
│   │   │   └── audit.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── companies.py
│   │   │   ├── users.py
│   │   │   ├── faq.py
│   │   │   ├── documents.py
│   │   │   ├── datasets.py
│   │   │   ├── chat.py
│   │   │   └── audit.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── company_service.py
│   │   │   ├── user_service.py
│   │   │   ├── faq_service.py
│   │   │   ├── document_service.py
│   │   │   ├── dataset_service.py
│   │   │   ├── chat_service.py
│   │   │   └── audit_service.py
│   │   ├── llm/
│   │   │   ├── ollama_client.py
│   │   │   ├── prompts/
│   │   │   │   ├── answer_prompt.txt
│   │   │   │   ├── sql_prompt.txt
│   │   │   │   └── classify_prompt.txt
│   │   │   ├── retrieval/
│   │   │   │   ├── faq_retriever.py
│   │   │   │   ├── rag_retriever.py
│   │   │   │   ├── sql_planner.py
│   │   │   │   └── reranker.py
│   │   │   └── embeddings/
│   │   │       └── embedding_client.py
│   │   ├── ingestion/
│   │   │   ├── pdf_parser.py
│   │   │   ├── chunker.py
│   │   │   ├── csv_importer.py
│   │   │   ├── schema_mapper.py
│   │   │   └── validators.py
│   │   ├── repositories/
│   │   │   ├── company_repo.py
│   │   │   ├── user_repo.py
│   │   │   ├── faq_repo.py
│   │   │   ├── document_repo.py
│   │   │   ├── dataset_repo.py
│   │   │   ├── chat_repo.py
│   │   │   └── audit_repo.py
│   │   └── utils/
│   │       ├── file_helpers.py
│   │       ├── date_helpers.py
│   │       └── text_helpers.py
│   ├── tests/
│   ├── requirements.txt
│   └── alembic/
│
├── worker/
│   ├── jobs/
│   │   ├── process_pdf.py
│   │   ├── process_csv.py
│   │   ├── generate_embeddings.py
│   │   └── cleanup_jobs.py
│   ├── runner.py
│   └── requirements.txt
│
├── storage/
│   ├── uploads/
│   │   ├── companies/
│   │   │   └── {company_id}/
│   │   │       ├── pdf/
│   │   │       ├── csv/
│   │   │       └── temp/
│   └── exports/
│
├── infra/
│   ├── nginx/
│   ├── caddy/
│   ├── cloudflare/
│   ├── launchd/
│   ├── systemd/
│   └── scripts/
│       ├── start_backend.sh
│       ├── start_frontend.sh
│       ├── start_worker.sh
│       ├── backup_db.sh
│       └── restore_db.sh
│
├── docs/
│   ├── architecture.md
│   ├── api-spec.md
│   ├── database-schema.md
│   ├── deployment-mac-mini.md
│   ├── deployment-vps.md
│   └── roadmap.md
│
├── .env.example
├── README.md
└── .gitignore
```

---

## 3. Storage Structure by Company

```text
storage/uploads/companies/{company_id}/
├── pdf/
│   ├── emergency_manual_v3_2.pdf
│   ├── reporting_procedure.pdf
│   └── ...
├── csv/
│   ├── incident_reports_march.csv
│   ├── users_import.csv
│   └── ...
└── temp/
```

Why this is good:
- every company is isolated
- easier backup
- easier migration later
- easier cleanup

---

## 4. Database Organization Idea

Because the system uses row-level isolation, all important tables should include:

- `company_id`
- `created_at`
- `updated_at`
- `created_by`
- `status`

Main tables:
- companies
- users
- faq_items
- documents
- document_chunks
- datasets
- dataset_imports
- chat_sessions
- chat_messages
- audit_logs

---

## 5. Best Development Order

### Step 1
- backend auth
- company model
- user model

### Step 2
- create company
- create user under company
- login

### Step 3
- FAQ CRUD

### Step 4
- PDF upload + parse + chunk + embedding

### Step 5
- chat with FAQ + RAG

### Step 6
- CSV upload + import

### Step 7
- SQL planner + hybrid answer

### Step 8
- logs + audit + deployment

This order is best because it gives a usable product earlier.

---

## 6. Important Rule for the Developer

Keep these separated:

- API layer
- business / service logic
- LLM logic
- file ingestion
- database access
- frontend UI

Do **not** mix everything into one file.

### Bad
- `chat.py` doing routes + SQL + prompt + file parsing + DB writes

### Good
- route file
- service file
- retriever file
- repository file
- prompt file

---

## 7. Immediate MVP To-Do

Start with these folders first:

- `frontend/src/app`
- `backend/app/api`
- `backend/app/models`
- `backend/app/services`
- `backend/app/llm`
- `backend/app/ingestion`
- `storage/uploads/companies`
- `docs`

Then build this first:

1. login
2. create company
3. create user under company
4. add FAQ
5. upload PDF
6. ask chat question

That gives the first real MVP.
