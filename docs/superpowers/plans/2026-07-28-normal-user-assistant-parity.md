# Normal User Assistant Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Normal Users the same Assistant chat controls and AI Insights behavior as Admin users.

**Architecture:** Keep the change frontend-only. Remove role gates from the existing Assistant page while leaving backend organization and department policy enforcement unchanged.

**Tech Stack:** Next.js 15, React 19, TypeScript, Node.js assert checks

---

### Task 1: Add The Regression Check

**Files:**
- Modify: `frontend/scripts/check-assistant-chat-policy.ts`

- [x] **Step 1: Add failing role-parity assertions**

Append:

```ts
ok(
  !source.includes("isAdmin"),
  "assistant chat controls and diagnostics must be the same for admin and normal users"
);
ok(
  source.includes("Array.from(enabledSources),\n        aiInsights,\n        modelMode,"),
  "assistant must send the selected AI Insights and response mode for every user"
);
```

- [x] **Step 2: Run the check and confirm RED**

Run:

```bash
cd frontend
node scripts/check-assistant-chat-policy.ts
```

Expected: failure containing `assistant chat controls and diagnostics must be the same for admin and normal users`.

### Task 2: Remove Assistant Role Gates

**Files:**
- Modify: `frontend/src/app/dashboard/assistant/page.tsx`

- [x] **Step 1: Use only the authenticated user from the auth context**

Replace:

```tsx
const { isAdmin, user } = useAuth();
```

with:

```tsx
const { user } = useAuth();
```

- [x] **Step 2: Send the selected AI Insights state for every role**

Replace:

```tsx
isAdmin ? aiInsights : false,
```

with:

```tsx
aiInsights,
```

- [x] **Step 3: Display the existing diagnostics for every role**

Replace:

```tsx
{isAdmin && msg.role === "assistant" && (msg.model_tier || msg.response_time_ms) && (
```

with:

```tsx
{msg.role === "assistant" && (msg.model_tier || msg.response_time_ms) && (
```

- [x] **Step 4: Remove the `isAdmin` wrappers around the existing AI Insights and response-mode controls**

Keep the existing toggle and response-mode markup unchanged; remove only the two role-condition wrappers and their wrapper fragments.

- [x] **Step 5: Run the focused check and confirm GREEN**

Run:

```bash
cd frontend
node scripts/check-assistant-chat-policy.ts
```

Expected: `assistant_chat_policy_ok`.

### Task 3: Verify And Restart

**Files:**
- No code changes

- [x] **Step 1: Run all frontend policy checks**

Run:

```bash
cd frontend
for check in scripts/check-*.ts; do node "$check"; done
```

Expected: every script exits successfully.

- [x] **Step 2: Run the backend AI policy tests**

Run:

```bash
cd backend
.venv/bin/python -m unittest tests.test_chat_policy_contract
```

Expected: all tests pass.

- [x] **Step 3: Build the frontend**

Run:

```bash
cd frontend
npm run build
```

Expected: Next.js build exits successfully.

- [x] **Step 4: Restart all ANDAI services**

Run:

```bash
launchctl kickstart -k "gui/$(id -u)/com.andai.backend"
launchctl kickstart -k "gui/$(id -u)/com.andai.frontend"
launchctl kickstart -k "gui/$(id -u)/com.andai.tunnel"
```

Expected: all three commands exit successfully.

- [x] **Step 5: Verify local and production health**

Run:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsSI http://127.0.0.1:3000/dashboard/assistant
curl -fsSI https://andai.my/dashboard/assistant
```

Expected: backend health is successful and both Assistant requests return HTTP 200.
