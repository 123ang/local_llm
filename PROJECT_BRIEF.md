# Andai — project brief

Snapshot: **2026-10-24 MYT**, written by Codex from a full repo read, reviewed by Claude. Dated orientation, not a live dashboard: recheck Git and runtime before status claims. History lives in [CHANGELOG.md](CHANGELOG.md).

## What it is

Andai is a company knowledge assistant for full admins, organization admins, and normal users. The web platform combines company documents, FAQs, and structured data with a local LLM. The repository also contains Android client source and mobile planning documents. The owner or paying client is not stated in the repository.

## Where things are

- Local checkout: `/Users/123ang/andai-runtime/local_llm`.
- GitHub: `123ang/local_llm`, public; default branch `main` (facts 2026-10-24).
- Current branch: `codex/andai-bilingual-web` at `60fe7e1`; it is four commits ahead and one behind `origin/main` (facts 2026-10-24).
- Runtime copy: this checkout. `/Users/123ang/Desktop/Websites/local_llm` is a symlink to it; launchd services run from the same checkout (facts 2026-10-24).
- Public URLs checked on 2026-10-24: `https://andai.my` and `https://agentic.andai.my` returned HTTP 200. This confirms that pages answered, not that a user workflow passed (facts 2026-10-24).

## Technology

| Layer | Technology | Version | Source |
|---|---|---|---|
| Web | Next.js, React, TypeScript, Tailwind CSS | Next `^15.3.2`; React `^19.1.0`; TS `^5.8.3`; Tailwind `^4.1.6` | `frontend/package.json` |
| API | FastAPI, Uvicorn, Python | FastAPI `0.136.3`; Uvicorn `0.34.0`; Python `3.12+` documented | `backend/requirements.txt`; `README.md` |
| Database | PostgreSQL, SQLAlchemy async/sync, Alembic, pgvector | PostgreSQL 18 documented; SQLAlchemy `2.0.41`; Alembic `1.18.4`; live DB version unknown | `README.md`; `backend/requirements.txt`; `backend/app/llm/vector_store.py` |
| LLM and embeddings | Ollama; chat, SQL, and embedding models configured by environment | Defaults: `gemma4:latest`, `qwen2.5-coder:1.5b`, `nomic-embed-text`; model versions are not pinned | `backend/app/core/config.py`; `.env.example` |
| Authentication | JWT, `python-jose`, Passlib, bcrypt | `python-jose 3.5.0`; `passlib 1.7.4`; bcrypt `>=4.0.1,<4.1.0` | `backend/requirements.txt`; `backend/app/core/security.py` |
| Jobs/cache | Celery and Redis declared; active runtime use not confirmed | Celery `5.5.2`; Redis client `5.3.1` | `backend/requirements.txt`; `.env.example` |
| Android client | Java, Android Gradle Plugin, Gradle wrapper | Java 17; AGP `8.2.2`; Gradle `8.5`; compile/target SDK 34, min SDK 26 | `andai_mobile/android/build.gradle`; `andai_mobile/android/app/build.gradle`; `andai_mobile/android/gradle/wrapper/gradle-wrapper.properties` |
| Hosting | macOS launchd in observed runtime; nginx/systemd deployment guide is a separate template | Runtime versions not confirmed | facts 2026-10-24; `deploy/DEPLOY_ANDAI_MY.md`; `deploy/launchd/` |

## Architecture

- `backend/app/main.py` starts FastAPI, validates runtime settings, initializes database tables and pgvector, ensures a super-admin account, and mounts API routers.
- `backend/app/api/`, `services/`, `models/`, and `schemas/` implement authentication, tenant/department access, organizations, users, documents, FAQs, datasets, API connectors, chat, audits, evaluations, analytics, and status.
- `backend/app/llm/unified_query.py` coordinates permitted knowledge sources and Ollama. `backend/app/ingestion/` parses PDF/office files and imports CSV or SQL; vector retrieval uses PostgreSQL pgvector.
- Dataset imports create organization-scoped tables. Configuration separates application, text-to-SQL reader, and dataset importer database roles (`backend/app/core/config.py`, `deploy/postgres_roles.sql.example`).
- `frontend/src/app/` contains the public page, login, and dashboard. Shared auth, API, navigation, and language providers are in `frontend/src/lib/`; Next rewrites `/api/*` to the local FastAPI service (`frontend/next.config.ts`).
- English and Malay dictionaries and the language switch are in `frontend/src/locales/` and `frontend/src/lib/i18n-context.tsx`. The bilingual UI implementation is on the current branch, not `origin/main` (`d828fb4`).
- `frontend/src/app/dashboard/assistant/` renders evidence, answer audits, and exports. The ordinary assistant UI omits API connector sources; backend connector routes remain available to authorized clients (`docs/superpowers/specs/2026-07-14-api-ui-cleanup-and-user-manual-design.md`).
- `andai_mobile/android/` contains a native Java client. The mobile README describes iOS and Android, but the current tree has Android files only; the iOS plan is in `ios-app-todo.md`.
- `deploy/launchd/` has local shell scripts; `deploy/nginx/` and `deploy/DEPLOY_ANDAI_MY.md` document a Linux/nginx option. Runtime service names and URLs are from facts 2026-10-24.
- `investment/` holds a separate Kedah approved-investment data preparation workflow, scripts, and source files.

## Run, test, deploy

- Local backend: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` — documented, not verified (`README.md`). The README also documents `python -m alembic upgrade head` for migrations.
- Local frontend: `cd frontend && pnpm dev` — documented, not verified (`README.md`).
- Frontend scripts include `pnpm test:i18n`, `pnpm typecheck`, and `pnpm build` (`frontend/package.json`). Backend test files are under `backend/tests/`. No tests, builds, installs, or servers were run for this documentation.
- The repo's launchd helpers are in `deploy/launchd/`; `start-backend.sh` and `start-frontend.sh` use the Desktop symlink path and the frontend script starts `next dev`. `watchdog.sh` instead starts `next start`, which expects a built app. These scripts were read, not run.
- `deploy/DEPLOY_ANDAI_MY.md` documents a Linux/nginx deployment with `pnpm build` and `pnpm start`; it is not evidence that this target is deployed.
- Observed live state: launchd services `com.andai.backend`, `com.andai.frontend`, and `com.andai.tunnel` were running on 2026-10-24. Both public URLs above returned HTTP 200 that morning (facts 2026-10-24). No browser flow, API business operation, or deployed UI feature was verified.

## Status

### Live (verified)

- The three named launchd services were observed running from this checkout on 2026-10-24 (facts 2026-10-24).
- `https://andai.my` and `https://agentic.andai.my` returned HTTP 200 from this Mac on 2026-10-24. This is an HTTP response check, not business-flow verification (facts 2026-10-24).

### Built, not verified live

- Backend and web source implement role and department-aware knowledge management, chat, evaluations, analytics, audit, and exports (`backend/app/`, `frontend/src/`; `ANDAI_IMPROVEMENT_CHECKLIST.md` marks these features complete).
- The English/Malay web interface is implemented in the current branch (`d828fb4`; `frontend/src/locales/`, `frontend/src/lib/i18n-context.tsx`). Public HTTP 200 checks do not confirm that the bilingual UI was exercised.
- Android client source is present in `andai_mobile/android/`; no build or device check was run for this task.

### In progress

- `codex/andai-bilingual-web` contains the bilingual web work plus shared agent context. It is ahead four/behind one versus `origin/main`; no open PR was listed (facts 2026-10-24). Last commit: `60fe7e1` on 2026-10-24.
- `codex/sme-techpedia-phase1` contains SME Techpedia changes; it is ahead one/behind eleven, with no open PR listed. Last commit: `dca7cba` on 2026-08-05 (facts 2026-10-24).
- The user decision dated 2026-10-23 is to build the next mobile version in this Andai repository. The earlier `andai_swift` sibling was moved to Trash; do not route work there or recreate it. No framework choice or completed mobile migration was recorded in the old brief.

### Planned / backlog

- iOS URL configuration, authentication, chat, navigation, testing, and TestFlight remain unchecked in `ios-app-todo.md`; treat these as a plan, not delivered work.
- `docs/andai-my-role-access-todo.md` lists external API connectors, Word ingestion, live role-by-role browser QA, and a possible department dashboard as pending. Some statements may be stale against current source; see unknowns below.
- `docs/superpowers/plans/` contains older unchecked implementation checklists. Compare each against source before treating it as current work.

### Known issues and unknowns

- The source README is stale in places: it names `llama3`, says full PDF processing is future work, describes a simpler feature set, and has Windows-specific setup examples. Current configuration and parser source differ (`README.md`; `backend/app/core/config.py`; `backend/app/ingestion/`).
- `andai_mobile/README.md` describes both native iOS and Android, but the current checkout inventory contains Android source only. The next mobile framework and delivery date are unknown.
- The role-access TODO says Word ingestion and API connector implementation are pending, while current code includes `office_parser.py` and API connector routes/services. Live behavior and remaining scope were not verified.
- The design plan for bilingual web still labels implementation pending, while the feature exists on the current branch. The feature's live UI behavior is unverified (`docs/superpowers/specs/2026-08-05-andai-bilingual-web-design.md`; `d828fb4`).
- PostgreSQL, Redis, Ollama model availability, database contents/schema at runtime, backup/restore, and user workflows were not checked in this documentation task. The version in `README.md` is not live database evidence.
- This task ran no tests, builds, installs, or application checks.

## Decisions and rules

- 2026-10-23 user decision retained from the old brief: the next mobile version belongs in this repository; do not revive or route to the removed `andai_swift` checkout.
- `ANDAI_IMPROVEMENT_CHECKLIST.md` records the product decisions: Source Only is the default, only super-admins change company AI settings, SQL is visible to admins only, and citations use document name/page/excerpt or dataset/table name. The checklist also prioritizes PDF export.
- `AGENTS.md` is the shared project rules file; `CLAUDE.md` imports it. Keep deployed, implemented, planned, and unverified facts separate. Documentation updates follow the same-commit rule when committing project work.
- `docs/superpowers/specs/2026-07-14-api-ui-cleanup-and-user-manual-design.md` keeps backend API connectors for authorized technical clients while removing them from normal end-user source controls.

## Read next

- [README.md](README.md) — setup and API overview; check the stale statements above.
- [ANDAI_IMPROVEMENT_CHECKLIST.md](ANDAI_IMPROVEMENT_CHECKLIST.md) — trust, citation, evaluation, and export decisions.
- [docs/andai-my-role-access-todo.md](docs/andai-my-role-access-todo.md) — role access notes and outstanding items.
- [ios-app-todo.md](ios-app-todo.md) and [andai_mobile/README.md](andai_mobile/README.md) — mobile plans and current README claims.
- [docs/manuals/ANDAI_User_Manual.md](docs/manuals/ANDAI_User_Manual.md) — user-facing role workflows.
- [docs/superpowers/specs/](docs/superpowers/specs/) and [docs/superpowers/plans/](docs/superpowers/plans/) — dated design and implementation notes.
- [investment/approved_investment_llm_workflow.md](investment/approved_investment_llm_workflow.md) — investment data workflow.

## Keeping this brief current

Before answering, compare this snapshot with current Git, source and runtime. If they disagree, say so; don't repeat a stale note as fact. After authorized work: add a CHANGELOG.md entry in the same commit, and update the affected facts here with the date and the evidence or checks actually run. Don't keep a competing status summary in any assistant's personal memory.
