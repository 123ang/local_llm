#!/usr/bin/env python3
"""Backfill pgvector embedding_vector from stored JSON embeddings."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from app.core.database import engine
from app.llm.vector_store import ensure_pgvector_schema


async def main() -> None:
    ok = await ensure_pgvector_schema()
    if not ok:
        raise SystemExit("pgvector schema setup failed")
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "UPDATE document_chunks "
            "SET embedding_vector = embedding::text::vector "
            "WHERE embedding IS NOT NULL AND embedding_vector IS NULL "
            "RETURNING id"
        ))
        rows = result.fetchall()
    print(f"Backfilled {len(rows)} pgvector embeddings")


if __name__ == "__main__":
    asyncio.run(main())
