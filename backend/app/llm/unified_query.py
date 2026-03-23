import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import engine
from app.core.logger import logger
from app.models.faq import FAQItem
from app.models.document import Document, DocumentChunk
from app.models.dataset import Dataset

STOPWORDS = {
    "what", "which", "where", "when", "who", "how", "why", "does", "did",
    "the", "a", "an", "is", "are", "was", "were", "been", "being", "have",
    "has", "had", "having", "do", "can", "could", "would", "should", "will",
    "shall", "may", "might", "must", "need", "for", "from", "with", "about",
    "into", "through", "during", "before", "after", "above", "below", "to",
    "of", "in", "on", "at", "by", "and", "but", "or", "not", "no", "so",
    "if", "then", "than", "that", "this", "these", "those", "it", "its",
    "you", "your", "our", "we", "they", "them", "their", "my", "me", "him",
    "her", "us", "i", "any", "some", "all", "each", "every", "both", "much",
}


async def unified_query(
    question: str,
    company_id: int | None,
    db: AsyncSession,
    enabled_sources: list[str] | None = None,
    ai_insights: bool = True,
    model_mode: str = "auto",
) -> dict:
    """
    Search selected knowledge sources (FAQ, documents, structured data)
    and combine into a single answer using the LLM.

    ``enabled_sources`` is a list such as ["faq", "documents", "database"].
    When *None* (default) all three are searched.
    When ``ai_insights`` is False, return raw retrieved data without LLM generation.
    """
    all_sources = {"faq", "documents", "database"}
    active = set(enabled_sources) & all_sources if enabled_sources is not None else all_sources

    sources = {"faq": [], "documents": [], "database": None}

    faq_evidence = []
    doc_evidence = []
    db_evidence = []

    # 1. FAQ search
    if company_id and "faq" in active:
        faq_results = await _search_faq(db, company_id, question)
        for faq in faq_results:
            faq_evidence.append(f"[FAQ] Q: {faq['question']}\nA: {faq['answer']}")
            sources["faq"].append(faq)

    # 2. Document semantic search
    if company_id and "documents" in active:
        doc_results = await _search_documents_semantic(db, company_id, question)
        for chunk in doc_results:
            doc_evidence.append(f"[Document: {chunk['source']}, page {chunk['page']}]\n{chunk['content']}")
            sources["documents"].append(chunk)

    # 3. Structured data (Text-to-SQL)
    if company_id and "database" in active:
        sql_result = await _query_structured_data(db, company_id, question)
        if sql_result and sql_result.get("row_count", 0) > 0:
            if isinstance(sql_result["result"], list) and sql_result["result"]:
                rows_text = _format_rows_for_llm(sql_result["result"])
                db_evidence.append(f"[Database query result — {sql_result['row_count']} rows returned]\n{rows_text}")
            elif isinstance(sql_result["result"], str) and "error" not in sql_result["result"].lower():
                db_evidence.append(f"[Database] {sql_result['result']}")
            sources["database"] = sql_result

    # Assemble evidence with smart filtering:
    # If DB returned good results, only include doc chunks with high relevance (>0.55)
    evidence = list(faq_evidence)

    if db_evidence:
        evidence.extend(db_evidence)
        high_quality_docs = []
        for i, chunk in enumerate(sources["documents"]):
            if chunk.get("score", 0) >= 0.55:
                high_quality_docs.append(doc_evidence[i])
        evidence.extend(high_quality_docs)
    else:
        evidence.extend(doc_evidence)

    # Build a short schema summary so the LLM always knows what data exists,
    # even when no rows matched the specific question.
    schema_summary = ""
    if company_id:
        ds_result = await db.execute(
            select(Dataset).where(Dataset.company_id == company_id, Dataset.is_queryable == True)
        )
        all_datasets = ds_result.scalars().all()
        if all_datasets:
            parts = []
            for ds in all_datasets:
                col_names = [c.get("name", "") for c in (ds.columns_schema or [])]
                parts.append(f'- {ds.display_name} ({ds.row_count} rows): columns {", ".join(col_names[:12])}')
            schema_summary = "Available database tables:\n" + "\n".join(parts)

    # 4. If user wants raw data only (no AI insights), return immediately
    if not ai_insights:
        if not evidence:
            return {
                "answer": "No matching data found. Try a different question or enable AI Insights for general knowledge answers.",
                "sources": sources,
                "model_tier": "instant",
            }
        return {"answer": "\n\n".join(evidence), "sources": sources, "model_tier": "instant"}

    # 5. Generate answer using LLM — ALWAYS call the model
    has_evidence = bool(evidence)
    if model_mode == "instant":
        use_fast = True
    elif model_mode == "thinking":
        use_fast = False
    else:
        # Auto mode: if user enabled any company sources (FAQ/docs/database), prefer instant mode.
        # Reserve thinking mode mainly for AI-only (no selected sources).
        use_fast = bool(active)

    try:
        from app.llm.ollama_client import generate

        if has_evidence:
            context = "\n\n".join(evidence)
            prompt = f"""Data:\n{context}

Question: {question}

Answer concisely. Use bullet points for tabular data. You may add a short insight."""
            system_msg = "You are ANDAI, a concise knowledge assistant. Present data clearly. Be brief."
        else:
            prompt = f"""{schema_summary}

No matching records found. Question: {question}

Answer from general knowledge. If relevant tables exist above, suggest how to rephrase."""
            system_msg = (
                "You are ANDAI, a concise knowledge assistant. "
                "No data? Use general knowledge. Never show SQL. Be brief."
            )

        answer = await generate(prompt, system=system_msg, fast=use_fast)
        model_tier = "instant" if use_fast else "thinking"
        return {"answer": answer, "sources": sources, "model_tier": model_tier}

    except ConnectionError:
        if evidence:
            combined = "\n\n".join(evidence)
            return {"answer": f"[LLM offline — showing raw results]\n\n{combined}", "sources": sources, "model_tier": "instant"}
        return {"answer": "The AI service is currently offline. Please try again later.", "sources": sources, "model_tier": "instant"}
    except Exception as llm_err:
        logger.error(f"LLM generation error: {llm_err}")
        if evidence:
            combined = "\n\n".join(evidence)
            return {"answer": f"[LLM error — showing raw results]\n\n{combined}", "sources": sources, "model_tier": "instant"}
        return {"answer": f"An error occurred while generating the answer. Please try again.", "sources": sources, "model_tier": "instant"}


def _format_rows_for_llm(rows: list[dict], max_rows: int = 30) -> str:
    if not rows:
        return "No results."
    cols = list(rows[0].keys())
    lines = [" | ".join(str(col) for col in cols)]
    for row in rows[:max_rows]:
        lines.append(" | ".join(str(row.get(c, "")) for c in cols))
    if len(rows) > max_rows:
        lines.append(f"... and {len(rows) - max_rows} more rows")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

async def _search_faq(db: AsyncSession, company_id: int, question: str) -> list[dict]:
    q_lower = question.lower()
    keywords = [w for w in q_lower.split() if len(w) > 2 and w not in STOPWORDS]
    if not keywords:
        return []

    result = await db.execute(
        select(FAQItem).where(FAQItem.company_id == company_id, FAQItem.is_published == True)
    )
    faqs = result.scalars().all()

    matches = []
    for faq in faqs:
        combined = (faq.question + " " + faq.answer).lower()
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            matches.append({"question": faq.question, "answer": faq.answer, "category": faq.category, "score": score})

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:3]


async def _search_documents_semantic(db: AsyncSession, company_id: int, question: str) -> list[dict]:
    """Semantic search with high relevance threshold."""
    result = await db.execute(
        select(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(DocumentChunk.company_id == company_id, Document.status == "ready")
    )
    chunks = result.scalars().all()
    if not chunks:
        return []

    chunks_with_embeddings = [c for c in chunks if c.embedding]

    if chunks_with_embeddings:
        try:
            from app.llm.embeddings.embedding_client import get_embedding, cosine_similarity

            query_embedding = await get_embedding(question)
            if not query_embedding:
                raise ValueError("Empty embedding")

            scored = []
            for chunk in chunks_with_embeddings:
                score = cosine_similarity(query_embedding, chunk.embedding)
                scored.append((score, chunk))

            scored.sort(key=lambda x: x[0], reverse=True)

            results = []
            for score, chunk in scored[:5]:
                if score > 0.5:  # Higher threshold — only genuinely relevant chunks
                    doc_result = await db.execute(select(Document).where(Document.id == chunk.document_id))
                    doc = doc_result.scalar_one_or_none()
                    doc_name = doc.original_name if doc else f"doc_{chunk.document_id}"
                    results.append({
                        "content": chunk.content[:600],
                        "source": doc_name,
                        "page": chunk.page_number,
                        "score": round(score, 3),
                    })
            return results

        except Exception as emb_err:
            logger.warning(f"Embedding failed — keyword fallback: {emb_err}")

    # Keyword fallback
    q_lower = question.lower()
    keywords = [w for w in q_lower.split() if len(w) > 2 and w not in STOPWORDS]
    if not keywords:
        return []

    scored_kw = []
    for chunk in chunks:
        score = sum(1 for kw in keywords if kw in chunk.content.lower())
        if score > 0:
            scored_kw.append((score, chunk))

    scored_kw.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, chunk in scored_kw[:5]:
        doc_result = await db.execute(select(Document).where(Document.id == chunk.document_id))
        doc = doc_result.scalar_one_or_none()
        doc_name = doc.original_name if doc else f"doc_{chunk.document_id}"
        results.append({
            "content": chunk.content[:600],
            "source": doc_name,
            "page": chunk.page_number,
            "score": score,
        })
    return results


async def _query_structured_data(db: AsyncSession, company_id: int, question: str) -> dict | None:
    """Text-to-SQL with sample rows for context and graceful error handling."""
    result = await db.execute(
        select(Dataset).where(Dataset.company_id == company_id, Dataset.is_queryable == True)
    )
    datasets = result.scalars().all()
    if not datasets:
        return None

    schema_desc = []
    for ds in datasets:
        cols = ds.columns_schema or []
        col_names = [c.get("name", "") for c in cols]
        col_details = ", ".join(f'"{n}" ({c.get("type", "text")})' for n, c in zip(col_names, cols))

        schema_desc.append(
            f'Table "{ds.table_name}" ({ds.row_count} rows): [{col_details}]'
        )

    schema_text = "\n".join(schema_desc)

    # Optional hint for common UUM-style tables so the LLM maps questions to the right columns
    table_hint = ""
    for ds in datasets:
        dname = (ds.display_name or "").lower()
        if "comment" in dname:
            table_hint += f'\n- Table "{ds.table_name}" (display: {ds.display_name}): student/course feedback; use course_id, course_name, lecturer_name, percentage, comment_text for questions about evaluations or what students said.'
        if "staff" in dname:
            table_hint += f'\n- Table "{ds.table_name}" (display: {ds.display_name}): staff directory; use no_staf, nama_staf_dan_gelaran, jawatan_akademik, pusat_pengajian for questions about lecturers or staff by school/department.'

    try:
        from app.llm.ollama_client import generate

        sql_prompt = f"""Tables:
{schema_text}{table_hint}

Q: "{question}"

Return ONLY a SELECT query (double-quote identifiers, LIMIT 100) or NONE."""

        sql = await generate(sql_prompt, system="PostgreSQL expert. Return only SQL, no explanation.", max_tokens=150, fast=True)
        sql = sql.strip()
        if sql.startswith("```"):
            sql = sql.strip("`").strip()
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()
        # Models often emit "SELECT ...;\nLIMIT 100" — the semicolon ends the first statement and breaks Postgres.
        sql = re.sub(r";\s*\r?\n\s*", " ", sql)
        sql = re.sub(r"\s+", " ", sql).strip()
        sql = sql.rstrip(";`").strip()

        if not sql or sql.upper().strip() == "NONE" or not sql.upper().lstrip().startswith("SELECT"):
            return None

        try:
            async with engine.begin() as conn:
                res = await conn.execute(text(sql))
                rows = res.fetchmany(50)
                columns = list(res.keys())
                data = [dict(zip(columns, row)) for row in rows]
                return {"sql": sql, "result": data, "row_count": len(data)}
        except Exception as e:
            logger.warning(f"SQL execution failed: {e} | SQL: {sql}")
            # Don't crash — return empty so the LLM can still answer from other sources
            return None

    except ConnectionError:
        return None
