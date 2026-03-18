import httpx
import numpy as np
from app.core.config import settings
from app.core.logger import logger


async def get_embedding(text: str) -> list[float]:
    """Generate a single embedding vector for the given text using Ollama."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                json={"model": settings.EMBEDDING_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            return resp.json().get("embedding", [])
    except httpx.ConnectError:
        raise ConnectionError("Ollama is not running. Cannot generate embeddings.")
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    results = []
    for text in texts:
        emb = await get_embedding(text)
        results.append(emb)
    return results


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    a_np = np.array(a, dtype=np.float32)
    b_np = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(a_np) * np.linalg.norm(b_np)
    if denom == 0:
        return 0.0
    return float(np.dot(a_np, b_np) / denom)
