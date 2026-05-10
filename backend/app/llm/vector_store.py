from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from app.core.config import settings
from app.core.logger import logger

COLLECTION_NAME = "andai_document_chunks"


@lru_cache(maxsize=1)
def _get_collection():
    """Return a persistent Chroma collection, or None if Chroma is unavailable."""
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as exc:  # Chroma is optional; DB JSON fallback remains available.
        logger.warning(f"Chroma vector store unavailable; falling back to DB scan: {exc}")
        return None


def vector_store_available() -> bool:
    return _get_collection() is not None


def upsert_document_chunks(chunks: list[dict[str, Any]]) -> int:
    """Upsert embedded document chunks into Chroma.

    Expected keys: id, document_id, company_id, content, page_number, embedding.
    """
    collection = _get_collection()
    if collection is None or not chunks:
        return 0

    valid = [c for c in chunks if c.get("embedding")]
    if not valid:
        return 0

    collection.upsert(
        ids=[f"chunk-{c['id']}" for c in valid],
        embeddings=[c["embedding"] for c in valid],
        documents=[c.get("content") or "" for c in valid],
        metadatas=[
            {
                "chunk_id": int(c["id"]),
                "document_id": int(c["document_id"]),
                "company_id": int(c["company_id"]),
                "page_number": int(c.get("page_number") or 0),
            }
            for c in valid
        ],
    )
    return len(valid)


def delete_document_vectors(document_id: int) -> None:
    collection = _get_collection()
    if collection is None:
        return
    try:
        collection.delete(where={"document_id": int(document_id)})
    except Exception as exc:
        logger.warning(f"Failed deleting Chroma vectors for document {document_id}: {exc}")


def query_document_chunks(
    *,
    company_id: int,
    query_embedding: list[float],
    limit: int = 5,
    min_score: float = 0.5,
) -> list[dict[str, Any]]:
    """Query Chroma and return chunk ids + cosine similarity scores.

    Chroma returns cosine distance for hnsw:space=cosine, so score = 1 - distance.
    """
    collection = _get_collection()
    if collection is None or not query_embedding:
        return []

    try:
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"company_id": int(company_id)},
            include=["metadatas", "distances"],
        )
    except Exception as exc:
        logger.warning(f"Chroma query failed; falling back to DB scan: {exc}")
        return []

    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    hits: list[dict[str, Any]] = []
    for metadata, distance in zip(metadatas, distances):
        score = 1.0 - float(distance)
        if score >= min_score:
            hits.append({
                "chunk_id": int(metadata["chunk_id"]),
                "document_id": int(metadata["document_id"]),
                "page_number": int(metadata.get("page_number") or 0),
                "score": score,
            })
    return hits
