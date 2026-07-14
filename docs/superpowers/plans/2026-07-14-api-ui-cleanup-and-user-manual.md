# ANDAI API UI Cleanup and User Manual Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove API snapshot features from the standard ANDAI web UI, preserve authenticated chat API access, and deliver a current role-based user manual with fresh screenshots.

**Architecture:** Make a frontend-only visibility cleanup for the obsolete API connector surfaces while leaving backend routes and database structures intact. Reuse the existing Playwright capture script and manual generator, updating both around three authenticated roles and one technical API appendix.

**Tech Stack:** Next.js 15, React 19, TypeScript, FastAPI, Playwright, Python, python-docx, ReportLab

---

### Task 1: Add a UI policy regression check

**Files:**
- Modify: `frontend/scripts/check-assistant-chat-policy.ts`
- Test: `frontend/scripts/check-assistant-chat-policy.ts`

- [ ] **Step 1: Add failing source-policy assertions**

Read `src/app/dashboard/assistant/page.tsx` and `src/app/dashboard/database/page.tsx`, then assert that the Assistant does not declare an `apis` source, neither page contains `API snapshots`, and Database does not render an `API Connectors` tab.

```ts
const databaseSource = readFileSync(join(process.cwd(), "src/app/dashboard/database/page.tsx"), "utf8");

ok(!source.includes('{ key: "apis"'), "assistant must not expose APIs as an end-user source");
ok(!source.includes("API snapshots"), "assistant must not describe API snapshots as knowledge evidence");
ok(!databaseSource.includes('label: "API Connectors"'), "database must not expose API connector controls");
```

- [ ] **Step 2: Run the check and verify it fails**

Run: `node frontend/scripts/check-assistant-chat-policy.ts`

Expected: assertion failure stating that the Assistant or Database still exposes an API surface.

- [ ] **Step 3: Keep the failing check for Task 2**

No implementation code changes in this task.

### Task 2: Remove API snapshot surfaces from the standard UI

**Files:**
- Modify: `frontend/src/app/dashboard/assistant/page.tsx`
- Modify: `frontend/src/app/dashboard/database/page.tsx`
- Test: `frontend/scripts/check-assistant-chat-policy.ts`

- [ ] **Step 1: Simplify the Assistant source selector**

Remove the `Plug` import and the `apis` item from `SOURCE_OPTIONS`. Change the source-only explanation to:

```tsx
Answer source: approved knowledge base. ANDAI will answer only from selected data, documents, or FAQ. If no evidence is found, it will refuse instead of using general knowledge.
```

- [ ] **Step 2: Remove the Database API connector UI**

Remove `api-connectors` from the `Tab` union, remove its tab entry, state, loader, form handlers, and JSX section. Keep table creation, table upload, data upload, row viewing, and dataset deletion unchanged. Do not edit backend API connector routes, migrations, services, or models.

- [ ] **Step 3: Run the source-policy check**

Run: `node frontend/scripts/check-assistant-chat-policy.ts`

Expected: `assistant_chat_policy_ok`.

- [ ] **Step 4: Build the frontend**

Run: `pnpm --dir frontend build`

Expected: successful Next.js production build with `/dashboard/assistant` and `/dashboard/database` generated.

### Task 3: Capture screenshots from all three roles

**Files:**
- Modify: `capture_manual_screenshots.cjs`
- Replace: `docs/assets/manual_screenshots/*.png`

- [ ] **Step 1: Make the capture script role-aware**

Accept separate environment credentials for `ASKAI_SUPER_ADMIN_*`, `ASKAI_ORG_ADMIN_*`, and `ASKAI_USER_*`. Reuse one helper to authenticate, create a browser context, seed local storage, and capture only pages allowed for that role.

```js
const ACCOUNTS = {
  superAdmin: credentials("ASKAI_SUPER_ADMIN"),
  orgAdmin: credentials("ASKAI_ORG_ADMIN"),
  user: credentials("ASKAI_USER"),
};
```

The script must fail before opening the browser if any credential pair is missing.

- [ ] **Step 2: Capture the agreed pages**

Use a consistent `1600x1200` desktop viewport and capture:

```text
01-login.png
02-full-admin-overview.png
03-full-admin-organizations.png
04-full-admin-users.png
05-full-admin-audit-logs.png
06-org-admin-overview.png
07-org-admin-documents.png
08-org-admin-faq.png
09-org-admin-database.png
10-org-admin-database-upload.png
11-org-admin-evaluations.png
12-org-admin-analytics.png
13-org-admin-users.png
14-org-admin-audit-logs.png
15-normal-user-assistant.png
```

- [ ] **Step 3: Run the capture script**

Run with the three local test accounts through `node capture_manual_screenshots.cjs`.

Expected: all 15 files are freshly written and every protected page loads its expected heading or assistant input.

- [ ] **Step 4: Inspect screenshot contact sheets**

Verify role-specific sidebars, readable content, no passwords or tokens, no API source chip, no `Try asking` prompts, and no API connector tab.

### Task 4: Rewrite and regenerate the user manual

**Files:**
- Modify: `docs/manuals/build_andai_user_manual.py`
- Generate: `docs/manuals/ANDAI_User_Manual.md`
- Generate: `docs/manuals/ANDAI_User_Manual.docx`
- Generate: `docs/manuals/ANDAI_User_Manual.pdf`

- [ ] **Step 1: Replace the manual content model**

Update the title metadata to Version 4.0 dated July 14, 2026. Organize instructions by Normal User, Organization Admin, and Full Admin. Reference the 15 new screenshot names and describe only the pages each role can access.

- [ ] **Step 2: Add the technical API appendix**

Document OAuth2 form login at `POST /api/auth/login` and authenticated chat at `POST /api/chat`. Use placeholders such as `YOUR_EMAIL`, `YOUR_PASSWORD`, and `YOUR_ACCESS_TOKEN`; do not embed working credentials or tokens. State that API requests obey the same organization and department permissions as the web UI.

- [ ] **Step 3: Remove obsolete manual content**

Remove API connector setup, synced response evidence, UI API source selection, old `Companies` wording, stale screenshots, and organization-specific example prompts.

- [ ] **Step 4: Generate all outputs**

Run the bundled workspace Python runtime against `docs/manuals/build_andai_user_manual.py`.

Expected: Markdown, DOCX, and PDF files are rewritten without missing-image warnings.

### Task 5: Verify the running application and document quality

**Files:**
- Verify: `frontend/.next/**`
- Verify: `docs/assets/manual_screenshots/*.png`
- Verify: `docs/manuals/ANDAI_User_Manual.{md,docx,pdf}`

- [ ] **Step 1: Restart ANDAI services**

Restart the existing launchd backend, frontend, and tunnel services. Do not alter service definitions.

- [ ] **Step 2: Run live health checks**

Verify HTTP 200 for local frontend `/dashboard/assistant`, local backend `/health`, and public `https://andai.my/dashboard/assistant`.

- [ ] **Step 3: Re-run policy and build checks**

Run:

```bash
node frontend/scripts/check-assistant-chat-policy.ts
pnpm --dir frontend build
```

Expected: policy check and build both exit successfully.

- [ ] **Step 4: Render document outputs for visual QA**

Use bundled document/PDF tooling. Avoid direct LibreOffice invocation under Codex. Inspect rendered pages for missing screenshots, clipping, overflow, unreadable captions, and stale API snapshot references.

- [ ] **Step 5: Review the final diff**

Confirm that backend API routes and connector persistence were not deleted, unrelated user changes remain untouched, and only the intended UI/manual files changed during this implementation.
