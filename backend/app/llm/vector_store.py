from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine
from app.core.logger import logger

VECTOR_DIMENSIONS = 768


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(v)) for v in values) + "]"


async def ensure_pgvector_schema() -> bool:
    """Ensure pgvector exists and document_chunks has an indexed vector column."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(text(
                f"ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_vector vector({VECTOR_DIMENSIONS})"
            ))
            await conn.execute(text(
                "UPDATE document_chunks "
                "SET embedding_vector = embedding::text::vector "
                "WHERE embedding IS NOT NULL AND embedding_vector IS NULL"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_vector_hnsw "
                "ON document_chunks USING hnsw (embedding_vector vector_cosine_ops)"
            ))
        return True
    except Exception as exc:
        logger.warning(f"pgvector schema unavailable; falling back to JSON embedding scan: {exc}")
        return False


async def pgvector_available(db: AsyncSession) -> bool:
    try:
        result = await db.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector')"))
        return bool(result.scalar())
    except Exception:
        return False


async def update_document_chunk_vectors(db: AsyncSession, chunk_ids: list[int]) -> int:
    """Copy JSON embeddings into the pgvector column for newly inserted chunks."""
    ids = [int(i) for i in chunk_ids if i is not None]
    if not ids:
        return 0
    id_list = ",".join(str(i) for i in ids)
    result = await db.execute(text(
        "UPDATE document_chunks "
        "SET embedding_vector = embedding::text::vector "
        f"WHERE id IN ({id_list}) AND embedding IS NOT NULL "
        "RETURNING id"
    ))
    return len(result.fetchall())


async def query_document_chunks(
    db: AsyncSession,
    *,
    company_id: int,
    query_embedding: list[float],
    limit: int = 5,
    min_score: float = 0.5,
) -> list[dict[str, Any]]:
    """Search document chunks with pgvector cosine similarity."""
    if not query_embedding:
        return []

    try:
        result = await db.execute(
            text(
                "SELECT dc.id AS chunk_id, dc.document_id, dc.page_number, "
                "1 - (dc.embedding_vector <=> CAST(:embedding AS vector)) AS score "
                "FROM document_chunks dc "
                "JOIN documents d ON d.id = dc.document_id "
                "WHERE dc.company_id = :company_id "
                "AND d.status = 'ready' "
                "AND dc.embedding_vector IS NOT NULL "
                "ORDER BY dc.embedding_vector <=> CAST(:embedding AS vector) "
                "LIMIT :limit"
            ),
            {
                "embedding": _vector_literal(query_embedding),
                "company_id": int(company_id),
                "limit": int(limit),
            },
        )
    except Exception as exc:
        logger.warning(f"pgvector query failed; falling back to JSON embedding scan: {exc}")
        return []

    hits: list[dict[str, Any]] = []
    for row in result.mappings().all():
        score = float(row["score"] or 0)
        if score >= min_score:
            hits.append({
                "chunk_id": int(row["chunk_id"]),
                "document_id": int(row["document_id"]),
                "page_number": int(row.get("page_number") or 0),
                "score": score,
            })
    return hits
