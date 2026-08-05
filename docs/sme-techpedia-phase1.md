# SME Techpedia Phase 1 Technical Note

## Objective

Deliver an AI-guided chatbot inside Techpedia that helps SME Bank users query Credit Technical policy/procedure material and selected FAQ content without allowing unsupported answers from general model knowledge.

## Requirements Mapping

| Requirement | Implementation |
| --- | --- |
| NLP interface for policy/procedure questions | Techpedia AI Assistant chat screen and `/api/chat` endpoint |
| Retrieve from approved internal policy documents | `documents.approval_status = approved`; retrieval filters approved and ready documents |
| Retrieve from selected FAQ database | FAQ retrieval uses published FAQ entries only |
| Structured/guided responses | Source-only system prompt and evidence packaging |
| Reference relevant document sections | PDF chunks store `section_title`; citations include document, section, and page |
| Click-through links to full policy/procedure docs | Frontend citation opens secured `/api/documents/{company_id}/{document_id}/file` with page anchor |
| Log interactions for audit | `chat_interaction` audit event stores question, answer, sources, response time, model tier, and source mode |
| Controlled knowledge framework | Backend clamps sources to `documents` and `faq`; AI Insights/general fallback forced off |
| Techpedia integration direction | Active app is now branded as Techpedia AI Assistant and scoped as an internal module |

## Architecture

```text
Techpedia Web UI
  -> Next.js Assistant module
  -> FastAPI /api/chat
  -> FAQ keyword retrieval
  -> Approved PDF semantic/keyword retrieval
  -> Local Ollama LLM source-only answer generation
  -> PostgreSQL chat/audit/document metadata
```

## Hardware Guidance For 200 Concurrent Users

Recommended production shape:

- App/API tier: 2 application nodes, 8 to 16 CPU cores each, 32 GB RAM each.
- LLM inference tier: dedicated GPU server with at least 1 high-memory GPU, preferably 48 GB VRAM or higher for 14B to 32B class models with concurrency batching.
- Database tier: PostgreSQL with 8 CPU cores, 32 GB RAM, fast NVMe storage, regular backups.
- Cache/queue tier: Redis for rate limiting, background processing, and session support.
- Storage: encrypted shared storage or object storage for approved PDFs.

For Phase 1, do not size by total users alone. Size by peak simultaneous chat generations, average token length, model size, and latency target. A Mac Studio can support prototype and small pilot use, but it is not the right production target for 200 concurrent bank users unless concurrency is heavily queued and latency expectations are relaxed.

## Recommended Phase 1 Model

For source-only policy Q&A, prioritize instruction-following, citation discipline, and efficient local serving over creative reasoning.

Good open-source candidates:

- Qwen2.5 14B Instruct or Qwen3 14B Instruct for balanced local performance.
- Llama 3.1 8B Instruct for lighter pilot hardware.
- Mixtral or larger Qwen/Llama variants only if a GPU server with enough VRAM is available.

Use `nomic-embed-text` or another approved local embedding model for document retrieval, with evaluation before production acceptance.

## Acceptance Checklist

- User cannot enable AI-only or general-knowledge answers.
- Chat request with `database` source is ignored by backend source policy.
- No evidence found returns a refusal instead of a hallucinated answer.
- Document answers include document name, section title when detected, and page number.
- Clicking a document citation opens the secured uploaded PDF.
- Every assistant answer creates a `chat_interaction` audit record.
- Only approved, ready documents are retrieved.
- Non-Phase 1 frontend routes are not exposed in navigation.
