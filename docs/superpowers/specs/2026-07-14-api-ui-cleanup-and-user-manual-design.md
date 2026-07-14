# ANDAI API UI Cleanup and User Manual Design

Date: 2026-07-14

## Goal

Keep ANDAI's everyday web interface focused on organization knowledge while preserving authenticated API access for technical users who need to test the LLM.

## Agreed Scope

- Remove the `APIs` source chip and all `API snapshot` wording from the Assistant UI.
- Remove the `API Connectors` tab and connector controls from the Database UI.
- Keep the existing backend API and connector implementation intact so this UI cleanup does not break external integrations or require a database migration.
- Rewrite the ANDAI user manual for Full Admin, Organization Admin, and Normal User audiences.
- Add a short, clearly separated `API Testing for Technical Users` appendix.
- Replace the existing screenshots with fresh captures from the current running application.
- Regenerate the Markdown, Word, and PDF manuals.

## UI Design

The Assistant source selector will show only:

- Database
- PDF / Docs
- FAQ

The source-only explanation will refer only to data, documents, and FAQ. The UI will no longer describe API responses as searchable evidence.

The Database page will retain table creation, table upload, data upload, row viewing, and dataset management. API connector state and controls will not be loaded or rendered by the page.

External API behavior remains available through authenticated backend routes. This preserves technical testing without presenting the API as a normal end-user knowledge source.

## Manual Structure

1. Purpose and role overview
2. Sign in and navigation
3. Normal User: start a chat, choose knowledge sources, read citations, and manage chat history
4. Organization Admin: overview, documents, FAQ, database, evaluations, analytics, users, and audit logs
5. Full Admin: organizations, departments, users, and platform audit logs
6. Troubleshooting
7. Suggested training flow
8. API Testing for Technical Users

The appendix will explain authentication and a minimal request to `POST /api/chat`. It will state that API access is for authorized technical testing, uses the same role and department controls as the web application, and is not an API-snapshot feature in the UI. Credentials and live access tokens will not be embedded in the manual.

## Screenshot Plan

Fresh screenshots will be captured at a consistent desktop viewport from the current local ANDAI deployment:

- Public sign-in page
- Full Admin overview
- Full Admin organizations and departments
- Full Admin users
- Full Admin audit logs
- Organization Admin overview
- Organization Admin documents
- Organization Admin FAQ
- Organization Admin database tables and upload flow
- Organization Admin evaluations and analytics
- Organization Admin users and audit logs
- Normal User assistant

Each protected screenshot will use a test account with the correct role. Screenshots will avoid exposing passwords, access tokens, or unrelated personal data.

## Data and Access Flow

- The web assistant submits only the three visible knowledge source keys.
- Existing backend authorization continues to enforce organization and department access.
- Technical users authenticate through `/api/auth/login` and submit questions through `/api/chat`.
- The manual documents the public contract only; internal model names and implementation details remain hidden.

## Error Handling

- Screenshot automation must stop with a clear error if a required role cannot sign in or a target page is unavailable.
- Manual generation must fail when a referenced screenshot is missing.
- The API appendix will cover common `401`, `403`, and no-evidence responses without publishing sensitive troubleshooting data.

## Verification

- Add a small source-level regression check proving the standard UI and manual contain no `APIs`, `API Connectors`, or `API snapshots` wording outside the technical appendix.
- Build the frontend.
- Restart ANDAI services and verify frontend, backend health, and the public assistant route.
- Capture and inspect every new screenshot for correct role navigation and readable layout.
- Generate Markdown, DOCX, and PDF outputs.
- Render the DOCX/PDF with bundled document tooling where available and visually inspect the pages for clipping, missing images, and stale UI.

## Out of Scope

- Deleting API connector database tables, migrations, services, or backend routes.
- Creating a public developer portal or API-key management UI.
- Changing the security design or adding new API authentication methods.
- Redesigning unrelated pages.
