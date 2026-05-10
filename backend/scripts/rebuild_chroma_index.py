#!/usr/bin/env python3
"""Rebuild the persistent Chroma vector index from stored DocumentChunk rows."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.core.database import async_session
from app.models.document import Document, DocumentChunk
from app.llm.vector_store import upsert_document_chunks, vector_store_available

BATCH_SIZE = 200


async def main() -> None:
    if not vector_store_available():
        raise SystemExit("Chroma vector store is unavailable")

    total = 0
    async with async_session() as db:
        result = await db.execute(
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.status == "ready", DocumentChunk.embedding.is_not(None))
            .order_by(DocumentChunk.id)
        )
        batch = []
        for chunk in result.scalars().all():
            batch.append({
                "id": chunk.id,
                "document_id": chunk.document_id,
                "company_id": chunk.company_id,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "embedding": chunk.embedding,
            })
            if len(batch) >= BATCH_SIZE:
                total += upsert_document_chunks(batch)
                batch.clear()
        if batch:
            total += upsert_document_chunks(batch)

    print(f"Indexed {total} document chunk vectors into Chroma")


if __name__ == "__main__":
    asyncio.run(main())
