# Techpedia AI Assistant - SME Phase 1

This branch turns the original prototype into a focused Phase 1 module for Techpedia: an AI-guided chatbot that answers only from approved policy/procedure documents and selected FAQ content.

## Phase 1 Scope

- Natural-language Q&A for SME Credit Technical policy and procedure references.
- Retrieval from approved uploaded PDFs and published FAQ entries.
- Source-only responses with document name, section title, page number, and FAQ evidence when available.
- Click-through document citations through the secured document endpoint.
- Full chat audit logging with question, answer, response time, model tier, source mode, and attached sources.
- Techpedia rebrand across the active backend/frontend surfaces.

Out of scope for Phase 1:

- Structured database question answering.
- AI-only/general-knowledge fallback.
- Analytics, evaluations, investor-demo pages, mobile app surfaces, and non-Techpedia prototype modules.

## Active Application Surface

- Frontend: `frontend/`
- Backend: `backend/`
- Active routes: overview, assistant, documents, FAQ, users, audit logs.
- Hidden/removed frontend routes: database, analytics, evaluations, companies.
- Backend routing exposes only auth, companies, users, FAQ, documents, chat, audit, and status APIs.

## Local Development

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

Default development admin:

```text
admin@techpedia.local / admin123
```

Set a strong `SECRET_KEY` and `SUPER_ADMIN_PASSWORD` before production deployment.

## Verification

Current lightweight Phase 1 policy tests:

```bash
cd backend
PYTHONPATH=. python3 -m unittest discover -s tests
```

Full application verification requires installed Python and Node dependencies plus a running PostgreSQL database and Ollama service.
