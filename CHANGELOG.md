# Changelog — Andai

What changed in this project, newest first. Claude Code, Codex and OpenClaw all read this file and add to it.

**Adding an entry:** in the same commit as the change, under today's `## YYYY-MM-DD` heading (create it at the top if missing).
One line per change: `- **Type:** what changed and why it matters (`<short hash>`; <branch if not default>; <who: user / Claude / Codex / OpenClaw>)`.
Types: Added, Changed, Fixed, Removed, Security, Deployed, Decision, Docs.
`Deployed` names the target and the evidence. `Decision` attributes it to the user. Don't record tests as passing unless they were run; write "checks: <what ran>".

## In progress (not on `main`)

- `codex/andai-bilingual-web`: English/Malay web interface plus shared agent context; four commits ahead and one behind `origin/main`, no open PR listed; last commit 2026-10-24 `60fe7e1` (facts 2026-10-24).
- `codex/sme-techpedia-phase1`: SME Techpedia phase 1 work; one commit ahead and eleven behind `origin/main`, no open PR listed; stale since last commit 2026-08-05 `dca7cba` (facts 2026-10-24).

## 2026-10-24

- **Docs:** Shared agent guidance and a dated project brief added to `main` (`6d91c44`; by user, Claude).
- **Docs:** Added this changelog and rewrote `PROJECT_BRIEF.md` from repo and supplied runtime evidence; no tests, builds, installs, or app checks were run (uncommitted; `codex/andai-bilingual-web`; Codex).

## 2026-08 (summary)

- **Added:** Added department RBAC and department-scoped source access (`bd57d5e`).
- **Added:** Added office document parsing and API connector backend support (`bd57d5e`).

## 2026-07 (summary)

- **Docs:** Recorded the API UI cleanup and manual refresh design, then implementation plan (`00d1b8c`, `bb75552`).
- **Docs:** Added account selection/upload-loader plan, code-first technical report design, and normal-user assistant parity design (`cd670e7`, `7e6fadd`, `b30ddfb`).

## 2026-06 (summary)

- **Changed:** Updated chat, retrieval, PDF processing, and Ollama client behavior (`4578f59`).
- **Security:** Hardened SQL imports, database roles, runtime settings, and API security; removed committed sample database and customer-like files (`1c10dca`).

## 2026-05 (summary)

- **Added:** Company trust settings, answer evidence audit, evaluations, and usage analytics (`36eaf31`, `e10b502`).
- **Added:** Executive answer presentation and PDF/Word/briefing exports; completed the recorded export polish backlog (`ca2f4c9`, `4b5d7d5`, `3e3dd42`).
- **Removed:** Removed the earlier iOS source tree while retaining the Android app source (`aa12e5e`).

## 2026-04 (summary)

- **Added:** Added native Android client source (`9b85319`).
- **Added:** Added native iOS client source (`9b85319`).

## 2026-03 (summary)

- **Added:** Started the repository with platform architecture and product design documents (`2949715`, `ae6b8d8`).
- **Added:** Built the FastAPI/Next.js application, authentication, organization data, chat/retrieval, import workflows, and deployment files (`1903016`, `9d7d06a`).
- **Changed:** Moved the user manual and branding into docs, recorded benchmark material, and refined the retrieval and API behavior (`e285e82`, `af82dbe`, `f55d213`).
