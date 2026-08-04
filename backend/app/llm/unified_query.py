import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import text_to_sql_engine
from app.core.logger import logger
from app.models.faq import FAQItem
from app.models.document import Document, DocumentChunk
from app.models.dataset import Dataset
from app.models.api_connector import APIConnector

SQL_DANGEROUS_FUNCTIONS = {
    "current_setting",
    "dblink",
    "dblink_exec",
    "lo_export",
    "lo_import",
    "pg_advisory_lock",
    "pg_advisory_xact_lock",
    "pg_ls_dir",
    "pg_read_binary_file",
    "pg_read_file",
    "pg_sleep",
    "pg_stat_file",
    "set_config",
}
SQL_FORBIDDEN_NODES = tuple(
    node_type
    for node_type in (
        getattr(exp, name, None)
        for name in (
            "Alter",
            "Command",
            "Copy",
            "Create",
            "Delete",
            "Drop",
            "Grant",
            "Insert",
            "Into",
            "Lock",
            "Merge",
            "Set",
            "Transaction",
            "TruncateTable",
            "Update",
            "Use",
        )
    )
    if node_type is not None
)
SQL_QUERY_ROOTS = (exp.Select, exp.Union, exp.Intersect, exp.Except)

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
    department_ids: list[int] | None = None,
    ai_insights: bool = True,
    model_mode: str = "auto",
    document_min_relevance: float = 0.60,
    require_citations: bool = True,
) -> dict:
    """
    Search selected knowledge sources (FAQ, documents, structured data)
    and combine into a single answer using the LLM.

    ``enabled_sources`` is a list such as ["faq", "documents", "database"].
    When *None* (default) all three are searched.
    When ``ai_insights`` is False, strict evidence mode is used: answer only
    from selected sources, and refuse if no matching source evidence is found.
    """
    all_sources = {"faq", "documents", "database", "apis"}
    active = set(enabled_sources) & all_sources if enabled_sources is not None else all_sources
    department_ids = sorted({int(i) for i in (department_ids or [])})

    sources = {"faq": [], "documents": [], "database": None, "apis": []}

    faq_evidence = []
    doc_evidence = []
    db_evidence = []
    api_evidence = []

    # 1. FAQ search
    if company_id and department_ids and "faq" in active:
        faq_results = await _search_faq(db, company_id, department_ids, question)
        for faq in faq_results:
            faq_evidence.append(f"[FAQ] Q: {faq['question']}\nA: {faq['answer']}")
            sources["faq"].append(faq)

    # 2. Document semantic search
    if company_id and department_ids and "documents" in active:
        doc_results = await _search_documents_semantic(db, company_id, department_ids, question)
        for chunk in doc_results:
            doc_evidence.append(f"[Document: {chunk['source']}, page {chunk['page']}]\n{chunk['content']}")
            sources["documents"].append(chunk)

    # 3. Structured data (Text-to-SQL)
    if company_id and department_ids and "database" in active:
        sql_result = await _query_structured_data(db, company_id, department_ids, question)
        if sql_result:
            sources["database"] = sql_result
        if sql_result and (sql_result.get("blocked") or sql_result.get("error")):
            db_evidence.append(f"[Database query blocked]\n{sql_result.get('result', 'The structured data query was blocked by safety rules.')}")
        elif sql_result and sql_result.get("row_count", 0) > 0:
            if isinstance(sql_result["result"], list) and sql_result["result"]:
                rows_text = _format_rows_for_llm(sql_result["result"])
                db_evidence.append(f"[Database query result — {sql_result['row_count']} rows returned]\n{rows_text}")
            elif isinstance(sql_result["result"], str) and "error" not in sql_result["result"].lower():
                db_evidence.append(f"[Database] {sql_result['result']}")

    # 4. API connector snapshots
    if company_id and department_ids and "apis" in active:
        api_results = await _search_api_connectors(db, company_id, department_ids, question)
        for item in api_results:
            api_evidence.append(f"[API: {item['name']}]\n{item['content']}")
            sources["apis"].append(item)

    # Deterministic formatting for key Kedah Investment demo questions.
    # Avoids bullet-list answers when the user specifically needs a table.
    if sources.get("database") and isinstance(sources["database"].get("result"), list):
        sql_text = (sources["database"].get("sql") or "").lower()
        rows = sources["database"].get("result") or []
        if "kedah_sector_jobs_per_rm1b" in sql_text and rows:
            return {
                "answer": _format_kedah_sector_jobs_table(rows),
                "sources": sources,
                "model_tier": "instant",
            }
        if "kedah_overall_jobs_per_rm1b_trend" in sql_text and rows and "union all" not in sql_text:
            row = rows[0]
            jobs = row.get("jobs_per_rm1b")
            total_emp = row.get("total_employment")
            total_inv = row.get("total_investment_rm_million")
            answer = (
                f"Based on the current trend, the estimated employment impact is **{float(jobs):,.2f} jobs per RM1 billion invested**.\n\n"
                f"| Metric | Value |\n|---|---:|\n"
                f"| Total employment used | {int(total_emp):,} |\n"
                f"| Total investment used | RM{float(total_inv):,.2f} million |\n"
                f"| Jobs per RM1 billion | {float(jobs):,.2f} |\n\n"
                "Note: calculated from location-level breakdowns to avoid double-counting; 2025 values are normalized from RM to RM million."
            )
            return {"answer": answer, "sources": sources, "model_tier": "instant"}

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
    evidence.extend(api_evidence)

    # Build a short schema summary so the LLM always knows what data exists,
    # even when no rows matched the specific question.
    schema_summary = ""
    if company_id and department_ids:
        ds_result = await db.execute(
            select(Dataset).where(
                Dataset.company_id == company_id,
                Dataset.department_id.in_(department_ids),
                Dataset.is_queryable == True,
            )
        )
        all_datasets = ds_result.scalars().all()
        if all_datasets:
            parts = []
            for ds in all_datasets:
                col_names = [c.get("name", "") for c in (ds.columns_schema or [])]
                parts.append(f'- {ds.display_name} ({ds.row_count} rows): columns {", ".join(col_names[:12])}')
            schema_summary = "Available database tables:\n" + "\n".join(parts)

    # 5. Strict evidence mode: do not answer outside selected sources.
    if not ai_insights:
        strict_evidence = _build_strict_evidence(faq_evidence, db_evidence, doc_evidence, api_evidence, sources, document_min_relevance)
        if not strict_evidence:
            return {
                "answer": _source_only_refusal(active),
                "sources": sources,
                "model_tier": "instant",
            }
        try:
            from app.llm.ollama_client import generate
            context = "\n\n".join(strict_evidence)
            prompt = f"""Source evidence:
{context}

Question: {question}

Answer using only the source evidence above. If the evidence does not contain the answer, say exactly: "I couldn't find that in the selected sources." Include source names/page numbers when available. Prefer Markdown tables for tabular data."""
            system_msg = (
                "You are ANDAI in Source-Only Mode. Use only the supplied source evidence. "
                "Do not use outside knowledge, assumptions, or general advice. If the answer is not in the evidence, refuse briefly."
            )
            answer = await generate(prompt, system=system_msg, fast=True)
            return {"answer": answer, "sources": sources, "model_tier": "instant"}
        except ConnectionError:
            return {"answer": "[AI offline — showing source evidence]\n\n" + "\n\n".join(strict_evidence), "sources": sources, "model_tier": "instant"}
        except Exception as llm_err:
            logger.error(f"Source-only generation error: {llm_err}")
            return {"answer": "The AI service encountered an error. Displaying source evidence directly:\n\n" + "\n\n".join(strict_evidence), "sources": sources, "model_tier": "instant"}

    # 6. Generate answer using LLM — AI Insights may use general knowledge only when no sources match.
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

Answer concisely. If the data is tabular or the user asks for a table/jadual/table format, use a Markdown table instead of bullet points. You may add a short insight."""
            system_msg = "You are ANDAI, a concise knowledge assistant. Present data clearly. Prefer Markdown tables for tabular data. Be brief. Ground factual claims in the supplied data."
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
            return {"answer": f"The AI service is currently offline. Displaying source data directly:\n\n{combined}", "sources": sources, "model_tier": "instant"}
        return {"answer": "The AI service is currently offline. Please try again later.", "sources": sources, "model_tier": "instant"}
    except Exception as llm_err:
        logger.error(f"LLM generation error: {llm_err}")
        if evidence:
            combined = "\n\n".join(evidence)
            return {"answer": f"The AI service encountered an error. Displaying source data directly:\n\n{combined}", "sources": sources, "model_tier": "instant"}
        return {"answer": "An error occurred while generating the answer. Please try again.", "sources": sources, "model_tier": "instant"}


def _format_kedah_sector_jobs_table(rows: list[dict], max_rows: int = 30) -> str:
    overall_rows = [r for r in rows if not r.get("sector") and r.get("jobs_per_rm1b") is not None]
    sector_rows = [r for r in rows if r.get("sector")]
    if not sector_rows:
        return "No sector data found."

    lines = []
    if overall_rows:
        overall = overall_rows[0]
        lines.extend([
            f"**Overall trend:** {float(overall.get('jobs_per_rm1b') or 0):,.2f} jobs per RM1 billion invested.",
            "",
        ])

    lines.extend([
        "Here is the estimated employment impact per RM1 billion invested by main sector:",
        "",
        "| Sector | Total Employment | Total Investment (RM million) | Jobs / RM1 billion |",
        "|---|---:|---:|---:|",
    ])
    for row in sector_rows[:max_rows]:
        sector = row.get("sector", "")
        emp = row.get("total_employment") or 0
        inv = row.get("total_investment_rm_million") or 0
        jobs = row.get("jobs_per_rm1b") or 0
        lines.append(f"| {sector} | {int(emp):,} | {float(inv):,.2f} | {float(jobs):,.2f} |")

    top = max(sector_rows, key=lambda r: float(r.get("jobs_per_rm1b") or 0))
    lines.append("")
    if len(sector_rows) == 1:
        lines.append(
            f"Insight: **{top.get('sector')}** records **{float(top.get('jobs_per_rm1b') or 0):,.2f} jobs per RM1 billion**."
        )
    else:
        lines.append(
            f"Insight: **{top.get('sector')}** has the highest estimate in this view, at **{float(top.get('jobs_per_rm1b') or 0):,.2f} jobs per RM1 billion**."
        )
    return "\n".join(lines)


def _build_strict_evidence(
    faq_evidence: list[str],
    db_evidence: list[str],
    doc_evidence: list[str],
    api_evidence: list[str],
    sources: dict,
    document_min_relevance: float = 0.60,
) -> list[str]:
    """Return evidence safe enough for Source-Only Mode."""
    evidence: list[str] = []
    evidence.extend(faq_evidence)
    evidence.extend(db_evidence)
    evidence.extend(api_evidence)

    for i, chunk in enumerate(sources.get("documents") or []):
        score = chunk.get("score", 0)
        # Keyword fallback returns integer match counts; pgvector/JSON returns 0..1.
        is_strong_keyword = isinstance(score, int) and not isinstance(score, bool) and score >= 2
        is_strong_vector = not isinstance(score, int) and float(score or 0) >= document_min_relevance
        if is_strong_keyword or is_strong_vector:
            if i < len(doc_evidence):
                evidence.append(doc_evidence[i])

    return evidence


def _source_only_refusal(active_sources: set[str]) -> str:
    selected = ", ".join(sorted(active_sources)) if active_sources else "selected sources"
    return (
        f"I couldn't find that in the selected sources ({selected}).\n\n"
        "Source-Only Mode is enabled, so I can only answer from the selected documents, database, FAQ, or API snapshots. "
        "Please ask about the uploaded/company data, or enable AI Insights if you want a general answer."
    )


def _extract_sql_table_refs(sql: str) -> set[str]:
    statement = _parse_single_select(sql)
    if statement is None:
        return set()

    cte_names = {
        cte.alias_or_name.casefold()
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }
    return {
        table.name
        for table in statement.find_all(exp.Table)
        if table.name and table.name.casefold() not in cte_names
    }


def _sql_uses_only_allowed_tables(sql: str, allowed_tables: set[str]) -> bool:
    if not _is_safe_select_sql(sql):
        return False
    refs = _extract_sql_table_refs(sql)
    normalized_allowed = {table.casefold() for table in allowed_tables}
    return bool(refs) and {table.casefold() for table in refs}.issubset(normalized_allowed)


def _sanitize_generated_sql(sql: str) -> str | None:
    cleaned = (sql or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = cleaned.removesuffix("```").strip()
    if cleaned.lower().startswith("sql"):
        cleaned = cleaned[3:].strip()
    cleaned = _strip_sql_comments(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()
    if not cleaned:
        return None
    return cleaned


def _is_safe_select_sql(sql: str) -> bool:
    return _parse_single_select(sql) is not None


def _parse_single_select(sql: str):
    cleaned = _sanitize_generated_sql(sql)
    if not cleaned:
        return None
    try:
        statements = sqlglot.parse(cleaned, read="postgres")
    except ParseError:
        return None
    if len(statements) != 1 or not isinstance(statements[0], SQL_QUERY_ROOTS):
        return None

    statement = statements[0]
    if any(statement.find(node_type) is not None for node_type in SQL_FORBIDDEN_NODES):
        return None
    for table in statement.find_all(exp.Table):
        if table.db or table.catalog:
            return None
    for function in statement.find_all(exp.Func):
        function_name = (getattr(function, "name", "") or "").casefold()
        if function_name in SQL_DANGEROUS_FUNCTIONS:
            return None
    return statement


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n\r]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return sql


async def _execute_readonly_query(sql: str, params: dict | None = None, fetch_limit: int = 50) -> tuple[list[str], list[dict]]:
    if text_to_sql_engine is None:
        raise RuntimeError("TEXT_TO_SQL_DATABASE_URL is not configured")
    async with text_to_sql_engine.connect() as conn:
        async with conn.begin():
            await conn.execute(text("SET TRANSACTION READ ONLY"))
            await conn.execute(text("SET LOCAL statement_timeout = '5000ms'"))
            res = await conn.execute(text(sql), params or {})
            rows = res.fetchmany(fetch_limit)
            columns = list(res.keys())
            return columns, [dict(zip(columns, row)) for row in rows]


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

async def _search_faq(db: AsyncSession, company_id: int, department_ids: list[int], question: str) -> list[dict]:
    q_lower = question.lower()
    keywords = [w for w in q_lower.split() if len(w) > 2 and w not in STOPWORDS]
    if not keywords:
        return []

    result = await db.execute(
        select(FAQItem).where(
            FAQItem.company_id == company_id,
            FAQItem.department_id.in_(department_ids),
            FAQItem.is_published == True,
        )
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


async def _search_documents_semantic(db: AsyncSession, company_id: int, department_ids: list[int], question: str) -> list[dict]:
    """Semantic search with pgvector first, then JSON/keyword fallbacks."""
    try:
        from app.llm.embeddings.embedding_client import get_embedding, cosine_similarity
        from app.llm.vector_store import query_document_chunks

        query_embedding = await get_embedding(question)
        if not query_embedding:
            raise ValueError("Empty embedding")

        vector_hits = await query_document_chunks(
            db,
            company_id=company_id,
            department_ids=department_ids,
            query_embedding=query_embedding,
            limit=5,
            min_score=0.5,
        )
        if vector_hits:
            chunk_ids = [hit["chunk_id"] for hit in vector_hits]
            chunk_result = await db.execute(
                select(DocumentChunk, Document)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.id.in_(chunk_ids), Document.status == "ready")
            )
            by_id = {chunk.id: (chunk, doc) for chunk, doc in chunk_result.all()}
            results = []
            for hit in vector_hits:
                pair = by_id.get(hit["chunk_id"])
                if not pair:
                    continue
                chunk, doc = pair
                results.append({
                    "content": chunk.content[:600],
                    "source": doc.original_name,
                    "document_id": doc.id,
                    "company_id": doc.company_id,
                    "page": chunk.page_number,
                    "score": round(hit["score"], 3),
                })
            if results:
                return results

        # Fallback: in-process cosine scan over JSON embeddings.
        result = await db.execute(
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                DocumentChunk.company_id == company_id,
                DocumentChunk.department_id.in_(department_ids),
                Document.status == "ready",
                DocumentChunk.embedding.is_not(None),
            )
        )
        chunks_with_embeddings = result.scalars().all()
        scored = []
        for chunk in chunks_with_embeddings:
            score = cosine_similarity(query_embedding, chunk.embedding)
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored[:5]:
            if score > 0.5:
                doc_result = await db.execute(select(Document).where(Document.id == chunk.document_id))
                doc = doc_result.scalar_one_or_none()
                doc_name = doc.original_name if doc else f"doc_{chunk.document_id}"
                results.append({
                    "content": chunk.content[:600],
                    "source": doc_name,
                    "document_id": doc.id if doc else chunk.document_id,
                    "company_id": doc.company_id if doc else chunk.company_id,
                    "page": chunk.page_number,
                    "score": round(score, 3),
                })
        if results:
            return results

    except Exception as emb_err:
        logger.warning(f"Embedding/vector search failed — keyword fallback: {emb_err}")

    # Keyword fallback using PostgreSQL full-text search (avoids loading all chunks into Python)
    q_lower = question.lower()
    keywords = [w for w in q_lower.split() if len(w) > 2 and w not in STOPWORDS]
    if not keywords:
        return []

    try:
        fts_result = await db.execute(
            text(
                "SELECT dc.id, dc.content, dc.page_number, dc.document_id, dc.company_id, "
                "ts_rank(to_tsvector('simple', dc.content), plainto_tsquery('simple', :query)) AS rank "
                "FROM document_chunks dc "
                "JOIN documents d ON d.id = dc.document_id "
                "WHERE dc.company_id = :company_id AND d.status = 'ready' "
                "AND dc.department_id = ANY(:department_ids) "
                "AND to_tsvector('simple', dc.content) @@ plainto_tsquery('simple', :query) "
                "ORDER BY rank DESC LIMIT 5"
            ),
            {"company_id": int(company_id), "department_ids": department_ids, "query": " ".join(keywords)},
        )
        rows = fts_result.mappings().all()
    except Exception as fts_err:
        logger.warning(f"FTS keyword fallback failed: {fts_err}")
        return []

    if not rows:
        return []

    doc_ids = list({row["document_id"] for row in rows})
    doc_result = await db.execute(select(Document).where(Document.id.in_(doc_ids)))
    docs_by_id = {doc.id: doc for doc in doc_result.scalars().all()}

    results = []
    for row in rows:
        doc = docs_by_id.get(row["document_id"])
        results.append({
            "content": row["content"][:600],
            "source": doc.original_name if doc else f"doc_{row['document_id']}",
            "document_id": doc.id if doc else row["document_id"],
            "company_id": doc.company_id if doc else row["company_id"],
            "page": row["page_number"],
            "score": int(round(float(row["rank"]) * 10)) or 1,
        })
    return results


async def _search_api_connectors(db: AsyncSession, company_id: int, department_ids: list[int], question: str) -> list[dict]:
    q_lower = question.lower()
    keywords = [w for w in q_lower.split() if len(w) > 2 and w not in STOPWORDS]
    if not keywords:
        return []

    result = await db.execute(
        select(APIConnector).where(
            APIConnector.company_id == company_id,
            APIConnector.department_id.in_(department_ids),
            APIConnector.status == "active",
            APIConnector.last_response_text.is_not(None),
        )
    )
    connectors = result.scalars().all()

    matches = []
    for connector in connectors:
        response_text = connector.last_response_text or ""
        combined = " ".join(
            part for part in (connector.name, connector.description or "", response_text) if part
        ).lower()
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            matches.append({
                "id": connector.id,
                "name": connector.name,
                "department_id": connector.department_id,
                "status_code": connector.last_status_code,
                "synced_at": connector.last_synced_at.isoformat() if connector.last_synced_at else None,
                "content": response_text[:1200],
                "score": score,
            })

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:3]


async def _query_structured_data(db: AsyncSession, company_id: int, department_ids: list[int], question: str) -> dict | None:
    """Text-to-SQL with sample rows for context and graceful error handling."""
    result = await db.execute(
        select(Dataset).where(
            Dataset.company_id == company_id,
            Dataset.department_id.in_(department_ids),
            Dataset.is_queryable == True,
        )
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
    dataset_names_by_table = {ds.table_name: ds.display_name for ds in datasets}

    # Deterministic routing for cleaned Kedah Investment analytical views.
    # These questions are important demo questions and should not depend on fragile Text-to-SQL generation.
    q_lower = question.lower()
    current_question = question.split("Current user question:")[-1] if "Current user question:" in question else question
    current_q_lower = current_question.lower()
    table_names = {ds.table_name for ds in datasets}
    if "kedah_overall_jobs_per_rm1b_trend" in table_names and "kedah_sector_jobs_per_rm1b" in table_names:
        wants_rm1b_jobs = (
            ("rm1" in q_lower or "rm 1" in q_lower or "bilion" in q_lower or "billion" in q_lower)
            and ("pekerjaan" in q_lower or "peluang" in q_lower or "jobs" in q_lower or "employment" in q_lower)
        )
        wants_sector_table_followup = (
            ("table" in current_q_lower or "jadual" in current_q_lower)
            and ("format" in current_q_lower or "table" in current_q_lower or "jadual" in current_q_lower)
        )
        wants_top_sector = any(token in current_q_lower for token in ["top", "highest", "tertinggi", "paling tinggi"])
        wants_lowest_sector = any(token in current_q_lower for token in ["lowest", "terendah", "paling rendah"])
        limit_match = re.search(r"\btop\s+(\d+)\b", current_q_lower)
        sector_limit = int(limit_match.group(1)) if limit_match else (1 if ("highest" in current_q_lower or "tertinggi" in current_q_lower or "lowest" in current_q_lower or "terendah" in current_q_lower) else 100)
        sector_limit = max(1, min(sector_limit, 100))
        if (wants_rm1b_jobs and ("sektor" in q_lower or "sector" in q_lower or "industry" in q_lower)) or wants_sector_table_followup or wants_top_sector or wants_lowest_sector:
            order_dir = "ASC" if wants_lowest_sector else "DESC"
            sql = (
                "SELECT 'Overall trend' AS scope, NULL::text AS sector, total_employment, "
                "total_investment_rm_million, jobs_per_rm1b, methodology_note "
                "FROM kedah_overall_jobs_per_rm1b_trend "
                "UNION ALL "
                "SELECT 'Sector breakdown' AS scope, sector, total_employment, "
                "total_investment_rm_million, jobs_per_rm1b, "
                "'Sector ratio = total_employment / (total_investment_rm_million / 1000). 2025 values normalized from RM to RM million.' AS methodology_note "
                "FROM (SELECT sector, total_employment, total_investment_rm_million, jobs_per_rm1b FROM kedah_sector_jobs_per_rm1b "
                f"ORDER BY jobs_per_rm1b {order_dir} LIMIT :sector_limit) s "
                "ORDER BY scope, jobs_per_rm1b DESC"
            )
            columns, data = await _execute_readonly_query(sql, {"sector_limit": sector_limit})
            table_refs = sorted(_extract_sql_table_refs(sql))
            return {"sql": sql, "result": data, "row_count": len(data), "tables": table_refs, "datasets": [dataset_names_by_table.get(t, t) for t in table_refs]}
        if wants_rm1b_jobs:
            sql = (
                'SELECT total_employment, total_investment_rm_million, jobs_per_rm1b, first_year, latest_year, methodology_note '
                'FROM kedah_overall_jobs_per_rm1b_trend LIMIT 1'
            )
            columns, data = await _execute_readonly_query(sql)
            table_refs = sorted(_extract_sql_table_refs(sql))
            return {"sql": sql, "result": data, "row_count": len(data), "tables": table_refs, "datasets": [dataset_names_by_table.get(t, t) for t in table_refs]}

    # Optional hint for common UUM-style tables so the LLM maps questions to the right columns
    table_hint = ""
    for ds in datasets:
        dname = (ds.display_name or "").lower()
        if "comment" in dname:
            table_hint += f'\n- Table "{ds.table_name}" (display: {ds.display_name}): student/course feedback; use course_id, course_name, lecturer_name, percentage, comment_text for questions about evaluations or what students said.'
        if "staff" in dname:
            table_hint += f'\n- Table "{ds.table_name}" (display: {ds.display_name}): staff directory; use no_staf, nama_staf_dan_gelaran, jawatan_akademik, pusat_pengajian for questions about lecturers or staff by school/department.'
        if "kedah overall jobs" in dname or "rm1b trend" in dname:
            table_hint += f'\n- Table "{ds.table_name}" (display: {ds.display_name}): use for Kedah current-trend questions like jobs/peluang pekerjaan per RM1 billion/RM1 bilion investment overall. It is already cleaned and avoids double-counting.'
        if "kedah sector jobs" in dname:
            table_hint += f'\n- Table "{ds.table_name}" (display: {ds.display_name}): use for Kedah questions asking jobs/peluang pekerjaan per RM1 billion/RM1 bilion by sector/sektor utama.'
        if "kedah location jobs" in dname:
            table_hint += f'\n- Table "{ds.table_name}" (display: {ds.display_name}): use for Kedah questions asking where/kawasan/lokasi employment opportunities are concentrated.'

    try:
        from app.llm.ollama_client import generate

        sql_prompt = f"""Tables:
{schema_text}{table_hint}

Q: "{question}"

Return ONLY a SELECT query (double-quote identifiers, LIMIT 100) or NONE."""

        sql = await generate(sql_prompt, system="PostgreSQL expert. Return only SQL, no explanation.", max_tokens=150, fast=True)
        sql = _sanitize_generated_sql(sql) or ""
        if not sql or sql.upper().strip() == "NONE" or not _is_safe_select_sql(sql):
            return None

        allowed_tables = {ds.table_name for ds in datasets}
        if not _sql_uses_only_allowed_tables(sql, allowed_tables):
            logger.warning(f"Rejected SQL outside company dataset allowlist: {sql}")
            return {
                "sql": None,
                "result": "Structured data query was blocked by safety rules. Please narrow the question to this company's uploaded datasets.",
                "row_count": 0,
                "blocked": True,
            }

        try:
            columns, data = await _execute_readonly_query(sql)
            table_refs = sorted(_extract_sql_table_refs(sql))
            return {"sql": sql, "result": data, "row_count": len(data), "tables": table_refs, "datasets": [dataset_names_by_table.get(t, t) for t in table_refs]}
        except Exception as e:
            logger.warning(f"SQL execution failed: {e} | SQL: {sql}")
            return {
                "sql": None,
                "result": "Structured data query could not be completed safely. Please try again or contact an administrator.",
                "row_count": 0,
                "error": True,
            }

    except ConnectionError:
        return None
