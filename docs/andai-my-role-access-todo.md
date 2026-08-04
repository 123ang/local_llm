# ANDAI.my Role Access And Multi-Organization TODO

Date: 2026-06-26

Purpose: capture the UI and backend changes identified from the ANDAI.my screenshots so we can implement them later without losing the discussion.

## Implementation Status

Updated on 2026-06-27:

- Phase 1 UI cleanup implemented.
- Super Admin sidebar now excludes Assistant.
- Normal User sidebar now shows Assistant only.
- Admin role now has organization-scoped management navigation.
- `Companies` is renamed to `Organizations` in visible UI.
- Normal users no longer see model/response-mode controls.
- Status UI and status API no longer expose raw model names.
- Login and dashboard route guards now send users to their role-appropriate default page.

Updated on 2026-07-01:

- Department RBAC backend implementation added from `ROles.pdf`.
- Added Department and User Department Access data model.
- Knowledge sources now carry `department_id` and `visibility`.
- Chat retrieval now filters FAQ, documents, and datasets by granted departments.
- New users can be created with zero department access.
- Super Admin creates users and departments; Department Admin curates knowledge and assigns department grants.
- Status API/UI now includes GPU RAM shape and RAG service health without exposing model names.

Still pending for a later hardening pass:

- Real external API connector for GET, POST, and cURL knowledge sources.
- Word document ingestion; current document parser remains PDF-focused.
- Live role-by-role browser QA with real credentials/test users.
- Dedicated department-level dashboard if departments need separate metrics beyond the current organization overview.

## Goal

Move ANDAI.my from a prototype-style single admin interface into a proper multi-organization / multi-department knowledge platform.

The main direction is:

- Super Admin manages the whole platform.
- Organization or Department Admin manages only their own workspace data.
- Normal User only uses the assistant/chat experience.
- Documents, FAQ, database datasets, users, chats, and analytics must be isolated by organization/department.

## Role Structure

### Super Admin

Super Admin should be for platform-level management only.

Visible areas:

- Overview
- Organizations / Departments
- Users
- Audit Logs
- System Status

Remove or hide from Super Admin:

- Assistant daily chat workflow
- User-facing chat suggestions
- Technical model details

### Organization / Department Admin

This role is needed so each organization or department can manage its own data.

Visible areas:

- Department dashboard
- Documents
- FAQ
- Database / Datasets
- Evaluations, if enabled for that department
- Analytics for own organization/department only
- Users for own organization/department only
- Audit logs for own organization/department only

Rules:

- Cannot access another department's private data.
- Can manage only assigned organization/department.
- Can share approved data only if visibility rules allow it.

### Normal User

Normal user should have a clean chat-only experience.

Visible areas:

- Assistant
- Chat history
- Profile / sign out

Remove or hide:

- Documents
- FAQ
- Database
- Evaluations
- Analytics
- Companies / Organizations
- Users
- Audit Logs
- System Status
- Model mode controls

## Naming Changes

Rename `Companies` to a more generic term.

Preferred option:

- `Organizations`

Alternative option:

- `Workspaces`

Departments can sit under each organization, for example:

- HR
- Finance
- Credit
- BPPK
- IT

## Data Ownership Model

Every knowledge source should have ownership metadata.

Apply to:

- Documents
- FAQ items
- Database tables / datasets
- Chat sessions
- Uploaded files
- Analytics records
- Audit logs
- Users

Required fields:

- `organization_id`
- `department_id`, nullable if organization-wide
- `visibility`
- `created_by_user_id`
- `updated_by_user_id`

Suggested `visibility` values:

- `private`
- `department`
- `organization`
- `global`

Important rule:

HR data must not be visible to Finance, Credit, or other departments unless explicitly shared.

## Backend Access Control

Do not rely only on frontend menu hiding.

Every API endpoint must enforce:

- User role
- Organization ownership
- Department ownership
- Dataset visibility
- Document visibility
- FAQ visibility
- Chat session ownership

Important APIs to check:

- Auth / current user
- Companies / organizations
- Users
- Documents
- FAQ
- Datasets
- Chat
- Analytics
- Audit logs
- Status endpoints

Acceptance rule:

If a user guesses another department's API URL or ID, backend must still reject it.

## UI Changes

### Sidebar

Super Admin sidebar:

- Overview
- Organizations
- Users
- Audit Logs
- System Status

Organization / Department Admin sidebar:

- Overview
- Assistant, optional
- Documents
- FAQ
- Database / Datasets
- Evaluations, optional
- Analytics
- Users
- Audit Logs

Normal User sidebar:

- Assistant
- Chat History
- Profile / Sign out

### Dashboard

Add organization/department-level dashboard.

Metrics:

- Total documents
- FAQ items
- Datasets
- Chat sessions
- Active users
- Recent uploads
- Recent questions
- Answer success/refusal rate
- Usage by document or dataset

The current Super Admin overview should not be reused as-is for all users.

## Assistant Page Changes

Normal users should not see technical controls.

Hide or simplify:

- `Model mode`
- `Auto`
- `Instant`
- `Thinking`
- Raw model names
- Internal LLM model list

Better wording:

- `AI Engine: Online`
- `Answer source: Approved knowledge base`
- `Source-only mode is enabled`

Keep:

- New chat
- Chat history
- Ask box
- Source badges or citations

## System Status Wording

Do not expose model names like:

- `qwen`
- `gemma`
- `nomic`
- `phi`

Replace with:

- `LLM: Connected`
- `Embedding service: Connected`
- `Database: Connected`
- `Redis: Running`

Detailed model names can remain available only in developer/debug logs, not normal UI.

## Source-Only Behavior

Source-only should remain the default behavior.

Rules:

- Assistant answers only from approved documents, FAQ, or datasets.
- If no source is found, assistant refuses politely.
- Response should include source references where available.
- Normal users should not be able to disable source-only mode.

Suggested refusal wording:

> I could not find this information in the approved knowledge base.

## Implementation Phases

### Phase 1: UI Cleanup

- Hide Assistant from Super Admin if not needed.
- Hide admin menus from Normal User.
- Rename Companies to Organizations.
- Hide raw model names from dashboard/status UI.
- Simplify Assistant controls for Normal User.

### Phase 2: Role And Permission Backend

- Add organization/department ownership checks to all APIs.
- Add role-based endpoint guards.
- Prevent cross-department document, FAQ, dataset, and chat access.
- Add tests for unauthorized access.

### Phase 3: Data Ownership Migration

- Add missing ownership fields to documents, FAQ, datasets, chat sessions, and audit records.
- Backfill existing records to current default organization/department.
- Create visibility rules.

### Phase 4: Organization / Department Admin Dashboard

- Build department-level dashboard.
- Add scoped analytics.
- Add scoped user management.
- Add scoped audit logs.

### Phase 5: QA And Security Checks

- Test Super Admin, Organization Admin, Department Admin, and Normal User flows.
- Test direct API access between departments.
- Test chat source filtering.
- Test document and dataset isolation.
- Test audit log visibility.

## Acceptance Criteria

- Normal User only sees chat-related UI.
- Super Admin only sees platform-level management UI.
- Organization/Department Admin can manage own workspace only.
- Cross-department data is blocked at backend level.
- Raw model names are not shown in normal UI.
- Source-only mode cannot be disabled by Normal User.
- Chat answers only use assigned organization/department knowledge sources.
- Audit logs record user, organization, department, action, and timestamp.

## Open Questions

- Should the product use `Organizations` or `Workspaces` as the final label?
- Do users belong to one department only, or multiple departments?
- Should Super Admin be allowed to chat for testing/debugging only?
- Which datasets are global, and which are department-private?
- Should department admins be allowed to invite users directly?
- Should analytics be visible to department admins, organization admins, or both?
