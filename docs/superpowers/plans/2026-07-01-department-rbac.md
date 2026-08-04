# Department RBAC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ANDAI satisfy the role PDF by enforcing Superadmin, Department/Organization Admin, and User knowledge scopes in the backend and UI.

**Architecture:** Keep `companies` as the tenant boundary and add `departments` as the knowledge ownership boundary. Knowledge sources get `department_id` and `visibility`; users get explicit department grants, and chat retrieval filters by those grants.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, Next.js App Router, TypeScript, Tailwind CSS.

---

### Task 1: Department Data Model

**Files:**
- Create: `backend/app/models/department.py`
- Create: `backend/app/schemas/department.py`
- Create: `backend/alembic/versions/9f31c2d4e8a7_add_department_rbac.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/company.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/models/document.py`
- Modify: `backend/app/models/dataset.py`
- Modify: `backend/app/models/faq.py`
- Modify: `backend/app/models/chat.py`

- [ ] Add departments, user-department grants, `department_id`, and `visibility`.
- [ ] Backfill one default department per existing company and assign existing company users to it.

### Task 2: Backend Permission Helpers And Tests

**Files:**
- Create: `backend/tests/test_department_rbac_contract.py`
- Modify: `backend/app/core/dependencies.py`

- [ ] Write failing contract tests for zero-access users, grant filtering, and admin/superadmin boundaries.
- [ ] Add helpers to resolve granted departments and enforce department access.

### Task 3: Department And Grant APIs

**Files:**
- Create: `backend/app/api/departments.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/users.py`

- [ ] Superadmin creates departments and users.
- [ ] Department admins assign/revoke only departments they own.
- [ ] Department admins cannot create users.
- [ ] User output includes granted departments.

### Task 4: Knowledge Source Enforcement

**Files:**
- Modify: `backend/app/api/documents.py`
- Modify: `backend/app/api/faq.py`
- Modify: `backend/app/api/datasets.py`
- Modify: `backend/app/llm/unified_query.py`
- Modify: `backend/app/ingestion/pdf_processor.py`
- Modify: `backend/app/llm/vector_store.py`

- [ ] Knowledge admins upload sources only to departments they own.
- [ ] Normal users list and chat against granted departments only.
- [ ] Superadmin cannot curate knowledge through API endpoints.

### Task 5: Frontend Department UI

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/app/dashboard/companies/page.tsx`
- Modify: `frontend/src/app/dashboard/users/page.tsx`
- Modify: `frontend/src/app/dashboard/documents/page.tsx`
- Modify: `frontend/src/app/dashboard/faq/page.tsx`
- Modify: `frontend/src/app/dashboard/database/page.tsx`
- Modify: `frontend/src/app/dashboard/assistant/page.tsx`

- [ ] Add department creation under Organizations.
- [ ] Add user grant assignment.
- [ ] Add department selectors to knowledge upload/create screens.
- [ ] Hide user creation from department admins.

### Task 6: Verification

**Files:**
- Modify/add focused tests only where needed.

- [ ] Run backend unit tests.
- [ ] Run frontend navigation check.
- [ ] Run frontend build.
- [ ] Browser-smoke login/dashboard surfaces.
