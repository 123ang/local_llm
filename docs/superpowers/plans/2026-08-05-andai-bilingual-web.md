# ANDAI Bilingual Web Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent English/Bahasa Melayu interface switch to every ANDAI web page without changing backend, permission, RAG, or stored-data behavior.

**Architecture:** English and Malay JSON files provide matched translation keys. A root React provider supplies language state, interpolation, enum display helpers, and locale formatting; a shared switch is reused by the public page, login, and dashboard top bar.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript, JSON locale files, Node validation script, Tailwind CSS, Playwright browser verification, launchd.

---

## File Map

- Create `frontend/src/locales/en.json` and `frontend/src/locales/ms.json`: complete interface dictionaries.
- Create `frontend/scripts/check-i18n.mjs`: recursive key and empty-value validation.
- Create `frontend/src/lib/i18n-context.tsx`: provider, translation interpolation, language persistence, and locale formatting.
- Create `frontend/src/components/LanguageSwitch.tsx`: shared accessible `EN | BM` control.
- Modify `frontend/package.json`: add `test:i18n` and `typecheck` scripts.
- Modify `frontend/src/app/layout.tsx`: wrap AuthProvider with language provider.
- Modify `frontend/src/app/page.tsx` and `frontend/src/app/login/page.tsx`: translate public/auth surfaces.
- Modify `frontend/src/components/layout/Sidebar.tsx`, `Topbar.tsx`, and `frontend/src/app/dashboard/layout.tsx`: translate shared authenticated layout.
- Modify every page under `frontend/src/app/dashboard`: translate all interface-owned copy while preserving dynamic values and API payloads.

### Task 1: Locale Contract And Provider

- [ ] Create the English and Malay JSON dictionaries with identical nested keys for common, public, login, navigation, overview, assistant, documents, FAQ, database, evaluations, analytics, organisations, users, and audit surfaces.
- [ ] Write `check-i18n.mjs` to recursively compare keys, reject empty strings, and verify the required `common.language`, `common.english`, and `common.malay` keys.
- [ ] Run `node scripts/check-i18n.mjs` and verify it reports both dictionaries aligned.
- [ ] Create `i18n-context.tsx` with `Language = "en" | "ms"`, safe local-storage restoration, `document.documentElement.lang`, `t(key, values)`, and locale-aware date formatting.
- [ ] Create `LanguageSwitch.tsx` using `aria-pressed` buttons and stable compact dimensions.
- [ ] Add `test:i18n` and `typecheck` scripts to `frontend/package.json`.

### Task 2: Public, Login, And Shared Layout

- [ ] Add `LanguageProvider` outside `AuthProvider` in the root layout.
- [ ] Add the language switch and dictionary copy to the public navigation, hero, feature, process, architecture, call-to-action, and footer sections.
- [ ] Add the switch and translated labels, placeholders, password visibility text, loading state, and errors to Login.
- [ ] Translate sidebar section headings and role-filtered navigation labels.
- [ ] Add the shared switch to Topbar and translate its accessible labels.
- [ ] Translate the dashboard authorization loading state without changing redirects or role checks.

### Task 3: Overview, Assistant, And Knowledge Pages

- [ ] Translate Overview cards, quick actions, role-specific instructions, system-status labels, and status messages.
- [ ] Translate Assistant conversation controls, empty states, source controls, model modes, input placeholder, diagnostics labels, and local fallback errors while leaving questions and AI answers unchanged.
- [ ] Translate Documents upload overlay, filters, table labels, statuses, empty states, tooltips, and processing explanation.
- [ ] Translate FAQ forms, filters, publication labels, empty states, tooltips, and client-owned messages while leaving saved FAQ content unchanged.
- [ ] Translate Database tabs, import/create forms, tables, previews, schema labels, validation messages, and tooltips while leaving identifiers and data unchanged.

### Task 4: Administration And Reporting Pages

- [ ] Translate Evaluations headings, forms, metrics, table labels, results, export controls, and empty states while leaving test questions and expected values unchanged.
- [ ] Translate Analytics headings, metrics, source-use labels, list headings, refresh controls, and empty states.
- [ ] Translate Organisations forms, AI settings, departments, tables, tooltips, statuses, and empty states while leaving organisation/department names unchanged.
- [ ] Translate Users forms, role/status display labels, department access controls, tables, tooltips, and empty states while leaving names/emails unchanged.
- [ ] Translate Audit Logs headings, table labels, known action/resource display labels, refresh controls, and empty states while leaving unknown audit values unchanged.

### Task 5: Verification And Deployment

- [ ] Run `npm run test:i18n`, `npm run typecheck`, `npm run lint`, and `npm run build` in `frontend`.
- [ ] Run relevant backend role and chat-policy contract tests to confirm no permission or RAG behavior changed.
- [ ] Verify public, login, Super Admin, Organisation Admin, and Normal User screens in English and Malay at desktop and mobile sizes.
- [ ] Verify language persistence across navigation, refresh, login, and logout.
- [ ] Commit with `git commit -m "feat: add English and Malay ANDAI web interface"`.
- [ ] Restart only the ANDAI frontend service, then verify public routes, health, login, and representative role pages on `https://andai.my`.
