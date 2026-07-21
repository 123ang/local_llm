# Account Selection and Upload Loader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reset stale organization selection across authentication changes and block the ANDAI interface while a document file is uploading.

**Architecture:** Keep tenant selection enforced in the existing authentication and company-ID layers. Add a fixed upload-only overlay and a temporary `beforeunload` handler to the Documents page; background processing remains asynchronous and visible through existing status polling.

**Tech Stack:** Next.js 15, React 19, TypeScript, browser localStorage, Node assertion scripts

---

### Task 1: Add Failing Regression Checks

**Files:**
- Create: `frontend/scripts/check-upload-guard-policy.ts`
- Test: `frontend/scripts/check-upload-guard-policy.ts`

- [ ] **Step 1: Add source-contract assertions**

Read `src/lib/auth-context.tsx`, `src/lib/api.ts`, and `src/app/dashboard/documents/page.tsx`. Assert that authentication clears `askai_selected_company_id`, non-Full-Admin login stores the returned company, the Documents page installs `beforeunload`, renders a `fixed inset-0` overlay, and resets upload state in `finally`.

- [ ] **Step 2: Run the check and verify RED**

Run: `node scripts/check-upload-guard-policy.ts`

Expected: assertion failure because the authentication reset and blocking overlay do not exist yet.

### Task 2: Reset Organization Selection During Authentication

**Files:**
- Modify: `frontend/src/lib/auth-context.tsx:43-58`
- Modify: `frontend/src/lib/api.ts:24-30`
- Test: `frontend/scripts/check-upload-guard-policy.ts`

- [ ] **Step 1: Update successful login storage**

After receiving the login response, remove `askai_selected_company_id`. If the returned user is not `super_admin` and has a `company_id`, store that ID before updating React state.

- [ ] **Step 2: Update logout and automatic 401 cleanup**

Remove `askai_selected_company_id` alongside `token` and `user` in both explicit logout and automatic unauthorized-session handling.

- [ ] **Step 3: Run the focused check**

Run: `node scripts/check-upload-guard-policy.ts`

Expected: authentication assertions pass; upload-overlay assertions still fail.

### Task 3: Add Upload-Only Blocking Overlay

**Files:**
- Modify: `frontend/src/app/dashboard/documents/page.tsx:12-58,112-225`
- Test: `frontend/scripts/check-upload-guard-policy.ts`

- [ ] **Step 1: Protect refresh and navigation during transfer**

Add an effect keyed by `uploading`. While true, register a `beforeunload` listener that calls `preventDefault()` and sets `returnValue`; remove it in the effect cleanup.

- [ ] **Step 2: Guarantee upload-state cleanup**

Move `setUploading(false)` and file-input reset into `finally`, preserving the existing backend error alert.

- [ ] **Step 3: Render the blocking loader**

While `uploading`, render a `fixed inset-0 z-50` grey overlay with a spinning `Loader2`, an `Uploading document` heading, and `Please keep this page open until the upload completes.` The overlay covers navigation and page controls, uses `role="status"`, and exposes an accessible live message.

- [ ] **Step 4: Run focused checks and production build**

Run: `node scripts/check-upload-guard-policy.ts`

Expected: `upload_guard_policy_ok`.

Run: `npm run build`

Expected: successful Next.js compilation, type checking, and static page generation.

### Task 4: Verify and Restart ANDAI

**Files:**
- Verify only; no additional source files

- [ ] **Step 1: Run existing frontend policy checks**

Run: `node scripts/check-navigation-policy.ts`

Expected: `navigation_policy_ok`.

Run: `node scripts/check-assistant-chat-policy.ts`

Expected: `assistant_chat_policy_ok`.

- [ ] **Step 2: Test Airport Admin upload**

Log in through the local API as `airportadmin@andai.my`, upload the small Techpedia reference PDF to company 11 and department 13, confirm HTTP 201 and a document record, then delete the test document.

- [ ] **Step 3: Restart frontend, backend, and tunnel services**

Restart `com.andai.frontend`, `com.andai.backend`, and `com.andai.tunnel` with launchd.

- [ ] **Step 4: Verify endpoints**

Confirm the local backend health endpoint, local Documents page, and public `https://andai.my/dashboard/documents` each return HTTP 200.

Implementation files remain uncommitted because the current `main` worktree contains existing unrelated changes; only explicitly scoped documentation commits are permitted without further user instruction.
