# ANDAI Improvement Checklist

This checklist captures the next improvement phases before implementation. It intentionally excludes sample/demo company setup.

## Phase 1 — Trust & Anti-Hallucination

- [ ] Add company-level knowledge settings
  - [ ] Default mode: Source Only / AI Insights
  - [ ] Allowed sources: Database, PDFs, FAQ
  - [ ] Minimum document relevance threshold
  - [ ] Require citation toggle
- [ ] Add answer audit trail
  - [ ] Sources used
  - [ ] PDF/page references
  - [ ] Database dataset/table used
  - [ ] SQL query hidden behind expand button
  - [ ] Retrieval scores hidden behind expand button
- [ ] Improve refusal behavior
  - [ ] Clear “not found in selected sources” message
  - [ ] Suggest enabling AI Insights only if company allows it
  - [ ] Suggest which source type to upload/query

## Phase 2 — Better Citations

- [ ] Make PDF citations clickable
  - [ ] Open document preview
  - [ ] Jump to page if possible
- [ ] Show quoted excerpt under citation
- [ ] Show “Used X passages from Y document”
- [ ] Group duplicate citations from same PDF/page
- [ ] Add source badges
  - [ ] PDF
  - [ ] Database
  - [ ] FAQ
  - [ ] AI Insight

## Phase 3 — Admin Knowledge Settings

- [ ] Add backend model/table for company AI settings
- [ ] Add API endpoints to read/update settings
- [ ] Add frontend admin settings page/section
- [ ] Enforce settings in `/chat`
- [ ] Prevent normal company admins from changing unsafe/global settings if needed
- [ ] Add audit log when settings are changed

## Phase 4 — Evaluation/Test Panel

- [ ] Add saved test questions
  - [ ] Question
  - [ ] Expected answer/keywords
  - [ ] Expected source
  - [ ] Company/source scope
- [ ] Add “Run test” button
- [ ] Store results
  - [ ] Pass/fail
  - [ ] Answer
  - [ ] Sources used
  - [ ] Latency
  - [ ] Model tier
- [ ] Add regression test history
- [ ] Add export test results

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

- [ ] Track questions asked
- [ ] Track unanswered/refused questions
- [ ] Track source type used
- [ ] Track latency/model tier
- [ ] Dashboard
  - [ ] Most asked questions
  - [ ] Most used documents/datasets
  - [ ] Unanswered questions
  - [ ] Active users
  - [ ] Average response time

## Before Coding Checklist

- [ ] Decide default behavior: Source Only by default or AI Insights by default
- [ ] Decide who can change AI settings: super admin only or company admin too
- [ ] Decide whether SQL should be visible to admins only
- [ ] Decide citation format
- [ ] Decide if PDF preview/page jump is required now or later
- [ ] Decide export priority: PDF first or Word first
- [ ] Backup database before schema changes
- [ ] Commit current stable state before starting next phase
