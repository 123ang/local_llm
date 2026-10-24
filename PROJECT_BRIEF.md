# Andai — shared project brief

Verified source snapshot: **2026-10-23 21:16 MYT**. This is a dated orientation, not a live health dashboard or full code audit.

## Purpose and project location

Company knowledge assistant using FastAPI, Next.js, PostgreSQL and local LLM integration.

Source checkout on this Mac: `/Users/123ang/Desktop/Websites/local_llm`. Active branch at inspection: `codex/andai-bilingual-web`; HEAD: `d828fb495078`. Recheck Git and the actual worktree before answering current-status questions.

## Read next

- [README.md](README.md)
- [ANDAI_IMPROVEMENT_CHECKLIST.md](ANDAI_IMPROVEMENT_CHECKLIST.md)
- [docs/andai-my-role-access-todo.md](docs/andai-my-role-access-todo.md)
- [ios-app-todo.md](ios-app-todo.md)

Existing AGENTS.md/CLAUDE.md rules and canonical design/monetization documents remain authoritative for policy. This brief does not grant deployment, migration, deletion or messaging permission.

## Implemented source evidence

- [backend/app/api](backend/app/api): Authentication, company/user administration, documents, FAQs, datasets, chat and evaluation routes.
- [backend/app/llm/unified_query.py](backend/app/llm/unified_query.py): Unified knowledge query implementation.
- [frontend/src/app/dashboard](frontend/src/app/dashboard): Web dashboard and assistant screens.

These paths were inspected for source presence/structure. No application tests were rerun for this documentation setup; do not describe them as passing now.

## Observed runtime and verification limits

Observed running launchd services `com.andai.backend` and `com.andai.frontend`; their working directories are under `/Users/123ang/andai-runtime/local_llm`, a separate runtime copy. Public-domain and business-flow health were not checked in this pass.

## Planned work, uncertainties and decisions

User decision, 23 October 2026: build the next mobile version in this Andai repository. The obsolete sibling `andai_swift` folder, including its local Git history and uncommitted work, was moved to Trash. Do not route work there or recreate it. Existing mobile folders/plans in this repo need assessment before choosing the new implementation; no framework or completed mobile migration is implied.

## Keeping this brief current

Before a project answer, compare this snapshot with current Git, relevant source and actual runtime evidence. If they disagree, state the discrepancy; do not repeat a stale note as fact. After authorized project work, update only the affected implemented/planned/runtime facts here, with the date, file/command evidence and checks actually run. Preserve unknowns and mark proposals as proposals. Personal chat memories are historical context, not a substitute for current shared evidence. For status answers, cover implemented source, verified deployment, remaining/planned work and unverified items; give a separate opinion only after those facts.
