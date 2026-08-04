# ANDAI Bilingual Web Interface Design

**Date:** 2026-08-05  
**Status:** Approved direction, pending implementation plan

## Goal

Support English and Bahasa Melayu across the complete ANDAI web platform while preserving authentication, role permissions, organisation and department isolation, backend APIs, RAG behavior, AI answers, and uploaded data.

## Scope

The bilingual interface covers:

- Public ANDAI page
- Login page
- Shared sidebar and top bar
- Super Admin overview and management screens
- Organisation Admin overview and management screens
- Normal User overview and Assistant
- Assistant conversations, controls, diagnostics labels, loading states, and empty states
- Documents, FAQ, Database, Evaluations, Analytics, Organisations, Users, and Audit Logs
- Buttons, forms, dialogs, tables, filters, placeholders, status and role labels, validation messages, tooltips, empty states, loading states, and accessibility labels

The Android application is excluded.

## Preserved Behavior

The following must not be translated or changed automatically:

- AI answers and chat messages
- User questions
- Uploaded filenames and document contents
- Dataset names, table names, column names, SQL, and database values
- Organisation and department names
- User names and email addresses
- FAQ questions and answers entered by users
- API payloads, backend error contracts, permissions, and audit data

The selected interface language does not alter prompts sent to the AI engine.

## User Experience

A compact segmented control labelled `EN` and `BM` is available on every web surface.

- Public and Login pages display the control in the top navigation area.
- Authenticated pages display the control in the shared top bar.
- English is the default for a first-time visitor.
- Selecting `BM` immediately changes all interface-owned text to Bahasa Melayu.
- Selecting `EN` immediately restores English.
- The selection persists across navigation, login/logout, role changes, and refreshes in the same browser.
- The page `lang` attribute changes between `en` and `ms`.
- The control remains visible and usable on mobile layouts.

Dedicated `/en` and `/ms` routes are deferred.

## Architecture

### Locale Files

Create two JSON dictionaries:

- `frontend/src/locales/en.json`
- `frontend/src/locales/ms.json`

Keys are grouped by surface and responsibility:

- `common`
- `public`
- `login`
- `navigation`
- `overview`
- `assistant`
- `documents`
- `faq`
- `database`
- `evaluations`
- `analytics`
- `organizations`
- `users`
- `audit`

Both files must have identical recursive key structures. Dynamic labels that contain values use simple named interpolation tokens such as `{count}`, `{days}`, or `{name}`.

### Language Provider

Create a client-side provider that wraps the existing `AuthProvider` in the root layout. It owns:

- Current language: `en` or `ms`
- Language update function
- Translation function with named interpolation
- Browser-storage persistence
- Updating `document.documentElement.lang`
- Locale selection for interface-owned date and number formatting

English is used for the server and initial client render. A valid saved preference is restored after hydration. Invalid saved values and storage failures fall back safely to English without blocking the application.

### Shared Language Control

Create one reusable `LanguageSwitch` component. It uses two compact buttons with `aria-pressed` state and translated group labels.

The public page, Login page, and dashboard top bar reuse the same component. No page creates its own language state.

### Interface Translation

Each page consumes the provider and replaces embedded interface literals with translation keys. Existing state, API calls, routing, permission gates, and business logic remain in place.

Display helpers translate known interface enums without changing stored values:

- Roles: Normal User, Organisation Admin, Super Admin
- Statuses: active, inactive, online, connected, processing, ready, failed, and similar UI states
- Assistant modes and source labels
- Audit action and resource-type labels when the value is a known platform enum

Unknown or user-generated values are displayed unchanged.

## Data Flow

1. The web application initially renders in English.
2. The language provider restores a valid browser preference after hydration.
3. The user selects `EN` or `BM` from a shared switch.
4. The provider updates React state, browser storage, and the page language attribute.
5. All active interface components re-render using the selected dictionary.
6. Navigation and authentication flows retain the selected language through the root provider and browser preference.
7. API requests continue sending the same payloads as before.

## Error Handling

- Client-owned fallback errors are translated.
- Known backend errors may be mapped to translated friendly messages where an existing stable error code or condition is available.
- Unknown backend details and correlation identifiers remain unchanged so support information is not lost.
- Browser-storage failure affects persistence only; switching still works for the current page session.
- Missing translation keys fail validation before deployment.

## Validation And Testing

Add a dependency-free Node validation script that:

- Recursively compares English and Bahasa Melayu dictionary keys
- Rejects missing, extra, or empty translation values
- Verifies required language-control labels

Add `npm run test:i18n` in the frontend package.

Verification gates:

- `npm run test:i18n`
- TypeScript check
- ESLint
- Production Next.js build
- Existing backend policy and contract tests remain unchanged and continue to pass where relevant

Browser verification covers:

- Public page and Login in both languages
- Super Admin navigation and management pages
- Organisation Admin navigation and content-management pages
- Normal User overview and Assistant
- Language persistence across navigation and refresh
- Desktop and mobile layouts without clipped or overlapping text
- Public `andai.my` health and route checks after restart

## Deployment

Build and restart only the ANDAI frontend service unless implementation evidence shows a backend restart is required. Verify the public site after restart and clearly distinguish local build success from live deployment success.

## Future Phase

A later phase may add dedicated `/en` and `/ms` public routes with localized metadata, canonical links, and server-rendered language selection. The Android app may reuse the approved terminology in its own separate implementation.
