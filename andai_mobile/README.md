# ANDAI Mobile

Native mobile apps for the **Adaptive Neural Decision AI (ANDAI)** platform. Separate native implementations for iOS (Swift/SwiftUI) and Android (Java/Material Design 3).

Both apps connect to the same FastAPI backend and provide a full-featured mobile interface for the ANDAI knowledge platform.

## Project Structure

```
andai_mobile/
├── ios/                          # iOS app (Swift + SwiftUI)
│   └── ANDAI/
│       ├── ANDAI.xcodeproj/      # Xcode project
│       └── ANDAI/
│           ├── ANDAIApp.swift     # App entry point
│           ├── Models/            # Data models (Codable)
│           ├── Services/          # API client + Auth service
│           ├── Extensions/        # Color theme extensions
│           └── Views/             # SwiftUI views
│               ├── Auth/          # Login screen
│               ├── Dashboard/     # Tab bar + Overview
│               ├── Assistant/     # AI Chat interface
│               ├── Documents/     # PDF management
│               ├── FAQ/           # FAQ CRUD
│               ├── Database/      # Dataset browser
│               ├── Companies/     # Tenant management
│               ├── Users/         # User management
│               ├── Audit/         # Activity logs
│               └── Settings/      # Profile + config
│
└── android/                      # Android app (Java)
    ├── build.gradle              # Root Gradle config
    ├── settings.gradle
    └── app/
        ├── build.gradle          # App module config
        └── src/main/
            ├── AndroidManifest.xml
            ├── java/com/andai/mobile/
            │   ├── ANDAIApplication.java
            │   ├── api/          # API client (OkHttp)
            │   ├── models/       # Data models (Gson)
            │   ├── utils/        # Auth manager
            │   └── ui/           # Activities + Fragments
            │       ├── auth/     # Login activity
            │       ├── dashboard/# Main + Overview + Manage
            │       ├── assistant/# Chat fragment + adapter
            │       ├── documents/# Document management
            │       ├── faq/      # FAQ CRUD
            │       ├── database/ # Dataset browser
            │       ├── companies/# Tenant management
            │       ├── users/    # User management
            │       ├── audit/    # Activity logs
            │       └── settings/ # Profile + config
            └── res/
                ├── layout/       # XML layouts
                ├── drawable/     # Icons + backgrounds
                ├── values/       # Colors, themes, strings
                └── menu/         # Bottom navigation menu
```

## Features

Both apps include:

- **Login** — JWT authentication with secure token storage
- **Dashboard** — Stats overview with document, FAQ, dataset, and session counts
- **AI Assistant** — Full chat interface with:
  - Session management (create, switch, delete)
  - Source toggles (Database, Documents, FAQ)
  - AI Insights toggle
  - Model mode selector (Auto / Instant / Thinking)
  - Source badges on responses
  - Suggested questions
- **Documents** — Upload PDFs, view processing status, delete
- **FAQ** — Create, edit, delete FAQ items with publish/draft toggle
- **Database** — Browse datasets and preview rows
- **Companies** — Manage tenants (super admin)
- **Users** — Manage user accounts with role assignment
- **Audit Logs** — View activity history
- **Settings** — Profile, company switcher, server status check, logout

## Setup

### iOS

1. Open `ios/ANDAI/ANDAI.xcodeproj` in Xcode
2. Update the API base URL in `Services/APIService.swift`
3. Select your target device or simulator
4. Build and run (Cmd+R)

**Requirements:** Xcode 15+, iOS 17+, Swift 5.9+

### Android

1. Open the `android/` folder in Android Studio
2. Update the API base URL in `app/build.gradle` (`API_BASE_URL` in `buildConfigField`)
3. Sync Gradle
4. Build and run

**Requirements:** Android Studio Hedgehog+, JDK 17, Android SDK 34, minSdk 26

## API Configuration

Both apps default to `localhost` in debug mode:
- **iOS:** `http://localhost:8000/api`
- **Android:** `http://10.0.2.2:8000/api` (emulator localhost alias)

Update the production URLs before release builds.

## Design

Both apps follow the ANDAI web app's design system:
- Primary color: `#DC2626` (red)
- Dark sidebar/login gradient: `#1A1A2E` → `#16213E` → `#0F3460`
- Light content background: `#F8FAFC`
- Card style: White with `#E2E8F0` border, 16dp rounded corners
- System font (SF Pro on iOS, Roboto on Android)
