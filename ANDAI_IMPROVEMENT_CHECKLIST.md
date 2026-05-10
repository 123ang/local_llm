# ANDAI Improvement Checklist

This checklist captures the next improvement phases before implementation. It intentionally excludes sample/demo company setup.

## Phase 1 — Trust & Anti-Hallucination

- [x] Add company-level knowledge settings
  - [x] Default mode: Source Only / AI Insights
  - [x] Allowed sources: Database, PDFs, FAQ
  - [x] Minimum document relevance threshold
  - [x] Require citation toggle
- [x] Add answer audit trail
  - [x] Sources used
  - [x] PDF/page references
  - [x] Database dataset/table used
  - [x] SQL query hidden behind expand button
  - [x] Retrieval scores hidden behind expand button
- [x] Improve refusal behavior
  - [x] Clear “not found in selected sources” message
  - [x] Suggest enabling AI Insights only if company allows it
  - [x] Suggest which source type to upload/query

## Phase 2 — Better Citations

- [x] Make PDF citations clickable
  - [x] Open document preview
  - [x] Jump to page if possible
- [x] Show quoted excerpt under citation
- [x] Show “Used X passages from Y document”
- [ ] Group duplicate citations from same PDF/page *(defer polish)*
- [x] Add source badges
  - [x] PDF
  - [x] Database
  - [x] FAQ
  - [ ] AI Insight *(defer until executive answer UI)*

## Phase 3 — Admin Knowledge Settings

- [x] Add backend model/table for company AI settings
- [x] Add API endpoints to read/update settings
- [x] Add frontend admin settings page/section
- [x] Enforce settings in `/chat`
- [x] Prevent normal company admins from changing unsafe/global settings if needed
- [x] Add audit log when settings are changed

## Phase 4 — Evaluation/Test Panel

- [x] Add saved test questions
  - [x] Question
  - [x] Expected answer/keywords
  - [x] Expected source
  - [x] Company/source scope
- [x] Add “Run test” button
- [x] Store results
  - [x] Pass/fail
  - [x] Answer
  - [x] Sources used
  - [x] Latency
  - [x] Model tier
- [x] Add regression test history
- [ ] Add export test results *(defer export polish)*

## Phase 5 — Reports & Exports

- [ ] Generate PDF/document summary
- [ ] Generate board memo / briefing
- [ ] Export answer as PDF
- [ ] Export answer as Word/Docx
- [ ] Include citations in exports
- [ ] Include generated charts/tables in exports

## Phase 6 — Executive Answer UI

- [ ] Add structured answer layout
  - [ ] Key answer
  - [ ] Evidence
  - [ ] Table/chart
  - [ ] Confidence
  - [ ] Recommended action, only when AI Insights is on
- [ ] Add chart rendering for numeric database results
- [ ] Add collapsible raw data section
- [ ] Add copy/export buttons

## Phase 7 — Usage Analytics

- [x] Track questions asked
- [x] Track unanswered/refused questions
- [x] Track source type used
- [x] Track latency/model tier
- [x] Dashboard
  - [x] Most asked questions
  - [x] Most used documents/datasets
  - [x] Unanswered questions
  - [x] Active users
  - [x] Average response time

## Before Coding Checklist

- [x] Decide default behavior: **Source Only by default**
- [x] Decide who can change AI settings: **super admin only**
- [x] Decide whether SQL should be visible to admins only: **yes, admins only**
- [x] Decide citation format: **Documents:** `Source: <PDF name>, page <page> — quoted excerpt`; **Database:** `Source: <dataset/table name>`
- [x] Decide if PDF preview/page jump is required now or later: **required now**
- [x] Decide export priority: **PDF first**
- [x] Backup database before schema changes: `backups/askai_before_ai_settings_20260510_180242.dump`
- [x] Commit current stable state before starting next phase: `a3df99e`

## Post-Refresh Reminder

- [ ] After token/context refresh, continue with Phase 4–7:
  - [x] Evaluation/Test Panel
  - [ ] Reports & PDF-first exports
  - [ ] Executive Answer UI
  - [x] Usage Analytics

