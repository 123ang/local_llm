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
- [x] Group duplicate citations from same PDF/page
- [x] Add source badges
  - [x] PDF
  - [x] Database
  - [x] FAQ
  - [x] AI Insight

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
- [x] Add export test results

## Phase 5 — Reports & Exports

- [x] Generate PDF/document summary *(single-answer printable evidence report)*
- [x] Generate board memo / briefing
- [x] Export answer as PDF
- [x] Export answer as Word/Docx
- [x] Include citations in exports
- [x] Include generated tables in exports
- [x] Include generated charts in exports

## Phase 6 — Executive Answer UI

- [x] Add structured answer layout
  - [x] Key answer
  - [x] Evidence
  - [x] Table/chart
  - [x] Confidence
  - [x] Recommended action / insight block when present
- [x] Add chart rendering for numeric database results
- [x] Add collapsible raw data section
- [x] Add copy button
- [x] Add PDF export button

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

## Remaining To-Do / Polish Backlog

- [x] Group duplicate citations from the same PDF/page into one citation card
- [x] Add polished AI Insight badge when AI Insights contributes beyond strict source evidence
- [x] Add export for evaluation test results
- [x] Add board memo / executive briefing export
- [x] Add Word/Docx export
- [x] Add printed visual chart rendering in PDF exports

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

- [x] After token/context refresh, continue with Phase 4–7:
  - [x] Evaluation/Test Panel
  - [x] Reports & PDF-first exports
  - [x] Executive Answer UI
  - [x] Usage Analytics
