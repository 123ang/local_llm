# ANDAI iOS App — Development TODO

## Overview

A SwiftUI chat app for end users to interact with the ANDAI AI assistant.
Connects to the existing FastAPI backend (`/api/*`), shares the same database and auth system.

- **Target:** End users (chat only, no admin features)
- **UI framework:** SwiftUI
- **Minimum iOS:** 16.0
- **Distribution:** TestFlight first, App Store later
- **Backend:** Existing FastAPI at `https://<your-domain>/api`
- **Multi-host:** Not every user hits the same server. The app must let the user **choose or enter the backend domain** (e.g. production `https://andai.my` today; self-hosted or white-label domains later). One binary, many backends.

---

## Configurable backend URL (domain)

Different organizations or deployments use different hosts. Design this in from day one so you are not hard-coding `andai.my` only in release builds.

- [ ] **Single source of truth** — e.g. `ServerConfiguration` or `EnvironmentService` holding `baseURL` (the origin only, e.g. `https://andai.my` or `https://customer.example.com`)
- [ ] **Default** — ship a sensible default (e.g. `https://andai.my`) for App Store / TestFlight users who do not customize anything
- [ ] **User-editable** — Settings screen: “Server” or “Connect to” with:
  - Text field for host (full URL or hostname + scheme toggle)
  - Optional presets: “Production (andai.my)”, “Custom…”
  - “Save” / “Apply” — validate before saving
- [ ] **URL rules** — normalize input:
  - Require `https://` in production (reject plain `http` except dev builds if you allow local testing)
  - Strip trailing `/`; `APIClient` builds paths as `baseURL + "/api/..."` so you never get `//api`
  - Reject whitespace and invalid URLs with a clear error message
- [ ] **Persistence** — store chosen base URL in `UserDefaults` (or App Group if you add a widget later). It is not secret; Keychain is for tokens only
- [ ] **Security when switching hosts** — on server URL change: **clear JWT and cached user** and return to login (same user on wrong host is invalid; avoids token leakage confusion)
- [ ] **First-run flow** — optional: onboarding step “Enter your organization server” *before* login, or login first then Settings — pick one UX and document it
- [ ] **Deep link / QR (optional)** — e.g. `andai://server?url=https%3A%2F%2F…` or a QR that sets base URL for enterprise rollouts
- [ ] **Backend coordination** — ensure each deployment’s FastAPI allows your iOS app’s requests (`CORS_EXTRA_ORIGINS` / trusted hosts as needed for browser; mobile apps often use same-origin or custom headers — align with `backend` `FRONTEND_URL` / ops docs per domain)

---

## Phase 1 — Project Setup

- [ ] Create Xcode project (App template, SwiftUI lifecycle)
- [ ] Set bundle ID, team, and signing for TestFlight
- [ ] Set deployment target to iOS 16.0
- [ ] Create folder structure:
  ```
  ANDAI/
    App/              # App entry point, app-level config
    Models/           # Codable structs matching API responses
    Services/         # Networking layer (APIClient, AuthService, ChatService)
    Views/            # SwiftUI views organized by feature
      Auth/
      Chat/
      History/
      Settings/
    ViewModels/       # ObservableObject classes per screen
    Extensions/       # Date formatting, Color theme, String helpers
    Resources/        # Assets, colors, fonts
  ```
- [ ] Add app icon and launch screen
- [ ] Configure `.gitignore` for Xcode / Swift (exclude `DerivedData`, `.build`, `xcuserdata`)

---

## Phase 2 — Networking & Auth

### API Client

- [ ] Create `APIClient` using `URLSession` (async/await)
  - **Base URL from `ServerConfiguration`** (not a compile-time constant) — reads persisted domain; see **Configurable backend URL** above
  - Support dev override in DEBUG (e.g. `localhost` with ATS exception only in dev schemes)
  - Automatic `Authorization: Bearer <token>` header injection
  - JSON decoding with `JSONDecoder` (snake_case → camelCase key strategy)
  - Centralized error handling (network, 401, 403, 5xx)
- [ ] Create Codable models matching backend schemas:
  - `LoginRequest` / `LoginResponse` (token, user info)
  - `User` (id, email, role, company_id)
  - `ChatSession` (id, title, company_id, created_at, updated_at)
  - `ChatMessage` (id, role, content, sources, model_tier, created_at)
  - `ChatRequest` (question, company_id, enabled_sources, ai_insights, model_mode)
  - `ChatResponse` (answer, sources, model_tier)

### Authentication

- [ ] Login screen (email + password)
- [ ] Call `POST /api/auth/login` → store JWT token
- [ ] Store token securely in Keychain (use `KeychainAccess` SPM or write a small wrapper)
- [ ] Auto-logout on 401 response (token expired)
- [ ] Persist login across app launches (read token from Keychain on startup)
- [ ] Add `GET /api/auth/me` call on launch to verify token validity

### Backend reference

| Action | Method | Endpoint |
|---|---|---|
| Login | POST | `/api/auth/login` |
| Current user | GET | `/api/auth/me` |
| List sessions | GET | `/api/chat/sessions?company_id=X` |
| Get messages | GET | `/api/chat/sessions/{id}/messages` |
| Send message | POST | `/api/chat` |
| Delete session | DELETE | `/api/chat/sessions/{id}` |

---

## Phase 3 — Chat UI

### Chat Screen

- [ ] Message list (ScrollView + LazyVStack, pinned to bottom)
  - User messages: right-aligned bubble, accent color
  - AI messages: left-aligned bubble, secondary color
  - Timestamp below each message (relative: "2m ago")
  - Markdown rendering in AI responses (use `AttributedString` or a lightweight Markdown renderer)
- [ ] Input bar at bottom:
  - Multi-line `TextField` (expands up to ~4 lines)
  - Send button (disabled while empty or loading)
  - Loading indicator while waiting for response
- [ ] Call `POST /api/chat` with the user's question
- [ ] Handle streaming or non-streaming response (current backend returns full response)
- [ ] Show source badges if `sources` are returned (FAQ, Documents, Database)
- [ ] Show model tier indicator (instant vs thinking)
- [ ] Auto-scroll to newest message on send and receive
- [ ] Empty state: show suggested questions (same as web app)
  - "Which lecturers have the highest evaluation percentage?"
  - "Show me student comments for a course"
  - "What data or tables do we have?"
- [ ] Tap a suggestion → fill input and send

### New Chat / Session Management

- [ ] "New Chat" button in navigation bar → creates a fresh conversation
- [ ] Each conversation becomes a session on the backend

---

## Phase 4 — Chat History

- [ ] History list screen (shows past chat sessions)
  - Call `GET /api/chat/sessions?company_id=X`
  - Show session title (or first message preview), date
  - Pull-to-refresh
- [ ] Tap a session → load messages via `GET /api/chat/sessions/{id}/messages` → open chat screen
- [ ] Swipe-to-delete a session (`DELETE /api/chat/sessions/{id}`)
- [ ] Search/filter sessions (client-side filtering by title)

---

## Phase 5 — Navigation & App Structure

- [ ] Use `TabView` with two tabs:
  1. **Chat** — current / new conversation
  2. **History** — past sessions
- [ ] Or use `NavigationSplitView` (sidebar on iPad, stack on iPhone):
  - Sidebar: session list
  - Detail: chat view
- [ ] Settings screen (accessible from profile icon or gear icon):
  - **Server / domain** — show current API base URL; edit and save (with validation); optional “Reset to default (andai.my)”
  - Current user info (email, role, company)
  - App version
  - Logout button
- [ ] Handle deep linking (optional, for future push notification taps)

---

## Phase 6 — Polish & UX

- [ ] Dark mode support (use semantic colors from asset catalog)
- [ ] Haptic feedback on send
- [ ] Keyboard avoidance (input bar moves up with keyboard)
- [ ] Handle no-network state gracefully (show banner, disable send)
- [ ] Pull-to-refresh on history list
- [ ] Skeleton / shimmer loading states
- [ ] Accessibility labels on all interactive elements
- [ ] Support Dynamic Type (scalable fonts)

---

## Phase 7 — Testing

- [ ] Unit tests for `APIClient` (mock URLProtocol)
- [ ] Unit tests for ViewModels (mock service layer)
- [ ] UI tests for login flow
- [ ] UI tests for send message + receive response
- [ ] Test on multiple screen sizes (iPhone SE, iPhone 15 Pro, iPad)
- [ ] Test on iOS 16 and latest iOS

---

## Phase 8 — TestFlight Distribution

- [ ] Set up App Store Connect (app record, bundle ID, team)
- [ ] Configure signing with automatic provisioning
- [ ] Archive and upload first build from Xcode
- [ ] Add internal testers in App Store Connect
- [ ] Write TestFlight release notes for each build
- [ ] Collect feedback, iterate

---

## Phase 9 — Future Enhancements (Post-MVP)

- [ ] Biometric auth (Face ID / Touch ID) for app unlock
- [ ] Push notifications for new responses or system alerts
- [ ] Offline message queue (store unsent messages, retry on reconnect)
- [ ] Widget (iOS WidgetKit) showing recent chat summary
- [ ] Siri Shortcut integration ("Ask ANDAI about…")
- [ ] iPad-optimized layout with sidebar
- [ ] Streaming response support (SSE or WebSocket) for real-time token display
- [ ] Voice input (Speech framework → text → send as chat)
- [ ] App Store submission (screenshots, description, review guidelines)

---

## Dependencies (Swift Package Manager)

| Package | Purpose | Required? |
|---|---|---|
| [KeychainAccess](https://github.com/kishikawakatsumi/KeychainAccess) | Secure token storage | Recommended |
| [swift-markdown-ui](https://github.com/gonzalezreal/swift-markdown-ui) | Render Markdown in AI responses | Recommended |
| None others needed | URLSession + SwiftUI cover networking and UI | — |

Keep dependencies minimal. SwiftUI + URLSession + Keychain cover 95% of needs.

---

## Key Architecture Decisions

1. **MVVM pattern** — each screen gets a ViewModel (`@Observable` or `ObservableObject`) that owns the business logic and calls services.
2. **Protocol-based services** — `AuthServiceProtocol`, `ChatServiceProtocol` so ViewModels can be tested with mocks.
3. **No third-party networking library** — `URLSession` async/await is sufficient for REST calls.
4. **Token in Keychain, not UserDefaults** — tokens are sensitive credentials.
5. **One source of truth for auth state** — a shared `AuthManager` that publishes login state and the current user; views react to it.
6. **Configurable API base URL** — default `https://andai.my`, user-overridable for other deployments; changing URL clears session and forces re-login.

---

*Created for the ANDAI project — Swift iOS app connecting to the local_llm FastAPI backend.*
