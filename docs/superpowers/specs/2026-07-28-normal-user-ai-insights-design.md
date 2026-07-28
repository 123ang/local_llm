# Normal User Assistant Parity Design

## Goal

Make the Normal User Assistant chat behave like the existing Admin Assistant chat without adding new configuration flows or backend complexity.

## User Experience

Normal Users will have the same Assistant chat controls currently available to Admin users:

- Database, PDF / Docs, and FAQ source selection
- Source Only / AI Insights toggle
- Auto, Quick, and Deep response modes
- AI Insight labels on responses
- Response mode and response time indicators

The existing conversation list, source citations, department scope, and no-department chat behavior remain unchanged.

## Implementation

The change is limited to the Assistant frontend page:

- Remove the role check that forces `ai_insights` to `false` for Normal Users.
- Show the existing AI Insights control to all Assistant users.
- Show the existing response mode controls to all Assistant users.
- Show the existing model mode and response time indicators to all Assistant users.

No new UI component, API endpoint, database table, migration, or dependency is required.

## Authorization And Policy

This change does not weaken backend controls.

- Organization and department access continue to scope all knowledge retrieval.
- The backend continues to enforce the organization's `ai_insights_allowed` setting.
- A user cannot bypass an organization-level AI Insights restriction by changing the browser request.
- Existing authentication and chat-session ownership checks remain unchanged.

## Failure Behavior

- Source Only remains the initial frontend state.
- If AI Insights is unavailable under organization policy, the backend keeps the response source-bound.
- Existing chat request errors continue to appear as Assistant error messages.

## Verification

- Add a focused frontend policy check proving Assistant controls are not role-gated.
- Run the existing frontend policy checks.
- Run the backend chat-policy tests.
- Build the frontend.
- Verify the Assistant as Super Admin, Organization Admin, and Normal User.
- Restart the ANDAI backend, frontend, and tunnel services.
- Verify local health endpoints and the production Assistant page.
