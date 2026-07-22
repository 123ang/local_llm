# ANDAI Code-First Technical Report Design

## Objective

Produce a complete internal developer reference for the current ANDAI platform. The report must explain the implementation from source code outward, then connect those details through architecture, data-flow, deployment, and operational views.

## Audience

The primary audience is developers who will maintain, debug, extend, deploy, or take over ANDAI. The report assumes general web-development knowledge but no prior familiarity with this repository.

## Deliverables

- `docs/technical/ANDAI_Technical_Report.md`
- `docs/technical/ANDAI_Technical_Report.docx`
- `docs/technical/ANDAI_Technical_Report.pdf`
- `docs/technical/build_andai_technical_report.py`
- Supporting architecture, database, and sequence-diagram images under `docs/technical/assets/`

Markdown is the canonical source. Word and PDF are generated deliverables and must contain the same substantive content.

## Source of Truth

The report is grounded in:

1. Current backend, frontend, deployment, migration, and test files in the working tree.
2. The live PostgreSQL schema, including tables, columns, types, nullability, defaults, constraints, indexes, and foreign keys.
3. Current local runtime configuration with all secret values redacted.
4. Existing user manuals, deployment notes, proposals, and technical documents only where they agree with current code.

The working tree contains uncommitted implementation changes. The report therefore records the generation date, branch, HEAD commit, and dirty-worktree status instead of claiming that HEAD alone represents the documented system.

## Accuracy Labels

The report distinguishes system state explicitly:

- **Implemented:** present in the current code and supported by direct evidence.
- **Partially Implemented:** some required code exists, but the end-to-end capability is incomplete or not fully operational.
- **Recommended:** a proposed production improvement that is not represented as current behavior.
- **Historical/Unused:** code, dependency, or documentation that remains in the repository but is not part of the active path.

Known discrepancies between documentation, ORM models, Alembic migrations, and the live schema are called out rather than silently reconciled.

## Report Structure

### Part I: Repository and Runtime Baseline

1. Document control, scope, generation baseline, and reading guide.
2. Technology stack and exact runtime dependencies.
3. Repository directory and ownership map.
4. Active processes, ports, proxying, storage locations, and external services.

### Part II: Backend Code Reference

5. FastAPI entry point and application lifecycle.
6. Core configuration, database engines, security, authentication dependencies, rate limiting, probe detection, and logging.
7. SQLAlchemy model reference, one subsection per model.
8. Pydantic schema reference.
9. API router catalogue, one subsection per router and endpoint.
10. Service-layer functions and business rules.
11. Ingestion modules for PDF, DOCX, CSV, Excel, and SQL files.
12. LLM clients, prompts, unified querying, source-only behavior, citations, embeddings, vector search, and text-to-SQL.
13. Background and asynchronous processing behavior.

### Part III: Database Design

14. Database design principles and tenant boundaries.
15. Complete ER diagram.
16. Table-by-table data dictionary.
17. Primary keys, foreign keys, uniqueness, nullability, defaults, indexes, JSON fields, and timestamp behavior.
18. Cascade and deletion behavior.
19. Alembic migration lineage and live-schema comparison.
20. Dataset-created physical tables, PostgreSQL roles, and text-to-SQL isolation.
21. Backup, restore, migration, retention, and recovery considerations.

### Part IV: Frontend Code Reference

22. Next.js application structure, route map, layouts, and providers.
23. Authentication context, browser storage, organization selection, and API client.
24. Sidebar/navigation policy and role-specific views.
25. Dashboard, Assistant, Documents, FAQ, Database, Evaluations, Analytics, Users, Organizations, and Audit pages.
26. Shared rendering components, citations, export behavior, loading states, and error handling.

### Part V: End-to-End Architecture

27. System context and component architecture.
28. Trust boundaries and authorization flow.
29. Login and organization-selection sequence.
30. Document-upload and ingestion sequence.
31. Chat/RAG request sequence.
32. FAQ and database-query sequences.
33. Audit and evaluation data flows.
34. File, relational, and vector-storage architecture.

### Part VI: Deployment and Operations

35. Current macOS launchd deployment and Cloudflare tunnel path.
36. Repository deployment templates for nginx/systemd and their status.
37. Environment-variable catalogue with values redacted.
38. Build, migration, startup, restart, shutdown, and health-check procedures.
39. Logging, diagnostics, monitoring, backup, restore, and troubleshooting.

### Part VII: Quality, Risks, and Roadmap

40. Automated test inventory and coverage map.
41. Security controls and residual risks.
42. Performance characteristics and concurrency constraints.
43. Known limitations, stale documentation, unused dependencies, and technical debt.
44. Prioritized production roadmap, separated into critical, near-term, and later improvements.
45. Developer onboarding checklist and operational runbook.

### Appendices

- Complete endpoint and permission matrix.
- Role and department-access matrix.
- Environment-variable reference.
- HTTP status and error catalogue.
- Model and terminology glossary.
- Source-file index.
- Verification commands and report-generation instructions.

## Database Documentation Method

The generator captures structured metadata from SQLAlchemy model definitions, Alembic migrations, and PostgreSQL catalog queries. The report includes every application-owned table and identifies dynamically created dataset tables separately. The ER diagram shows tenant, department, user, knowledge, chat, audit, and evaluation relationships without exposing production data.

## Diagram Strategy

Diagrams are generated as image assets for consistent rendering in Markdown, Word, and PDF. Required diagrams are:

1. System context diagram.
2. Runtime component and deployment diagram.
3. Complete database ER diagram.
4. Authentication and authorization flow.
5. Document ingestion sequence.
6. Chat/RAG sequence.
7. Database-query and text-to-SQL trust-boundary flow.

Diagrams use restrained ANDAI branding, readable labels, and print-safe colors. They prioritize technical legibility over decoration.

## Security and Privacy Rules

- Never include passwords, password hashes, JWTs, API keys, database credentials, private headers, or secret environment values.
- Show environment-variable names and purposes; display sensitive values as `[REDACTED]`.
- Do not reproduce user chat content, uploaded-document content, or personal data from the live database.
- Database evidence is limited to schema metadata and safe aggregate counts where useful.
- Clearly identify local-development assumptions that are not appropriate for production.

## Generation and Maintenance

`build_andai_technical_report.py` is the reproducible source for Word and PDF outputs. It consumes the canonical Markdown and local diagram assets. The script fails when required diagrams are missing and keeps page headings, tables, code blocks, and captions consistent across formats.

## Quality Assurance

1. Cross-check each backend model, API router, service, ingestion module, frontend route, deployment file, and automated test against the source inventory.
2. Compare ORM and migration documentation with the live PostgreSQL schema.
3. Scan generated content for secrets and credential patterns.
4. Verify internal links, headings, tables, diagrams, and code blocks.
5. Render every Word and PDF page and inspect for clipping, overlap, unreadable diagrams, broken tables, orphaned headings, and blank pages.
6. Confirm Word and PDF page counts and substantive section coverage are consistent.

## Acceptance Criteria

- All requested deliverables exist and open successfully.
- The report is code-first and includes architecture as supporting explanation.
- Every application model and API router is documented.
- The complete database design and ER diagram reflect verified schema evidence.
- Current implementation, partial implementation, recommendations, and historical code are not conflated.
- No secret or personal value appears in any artifact.
- Word and PDF pass full visual render inspection.
- The report generator can reproduce both generated formats from the canonical Markdown and diagram assets.
