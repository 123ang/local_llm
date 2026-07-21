# ANDAI Account Selection and Upload Loader Design

## Goal

Prevent organization-scoped users from inheriting a company selection from a previous browser session, and clearly block interaction while a document file is transferring.

## Account Selection

- On successful login, clear the previous `askai_selected_company_id` value.
- For Organization Admin and Normal User accounts, store the organization assigned by the login response.
- For Full Admin accounts, leave the selection empty so an organization is chosen explicitly.
- On logout and automatic 401 handling, remove the selected organization together with the token and user data.
- Keep the existing runtime safeguard that ignores stored organization selections for non-Full-Admin users.

## Upload Experience

- When a user selects a PDF or DOCX file, immediately show a fixed full-screen grey overlay.
- The overlay contains a spinner, an `Uploading document` heading, and a short instruction to keep the page open.
- The overlay blocks pointer interaction with navigation and page controls during the file transfer.
- While uploading, register a `beforeunload` handler so refresh, tab close, and navigation trigger the browser's standard leave-page warning.
- Remove the handler and overlay in a `finally` block after upload success or failure.
- After the upload API accepts the file, return to the normal Documents page. Existing polling and status badges continue to show background parsing and indexing.
- On failure, remove the overlay and show the backend error message.

## Scope

No backend API, document processing, database schema, or authorization changes are required. The change is limited to frontend authentication storage, the Documents page, and focused regression checks.

## Verification

- A regression check confirms login, logout, and 401 handling reset the organization selection.
- A regression check confirms the Documents page has a blocking upload overlay and unload protection.
- The frontend production build passes.
- The Airport Organization Admin can upload a PDF to Airport Malaysia and the test document is removed afterward.
- Restart the frontend service and verify local and public Documents endpoints return HTTP 200.
