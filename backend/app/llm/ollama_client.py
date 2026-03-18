import httpx
from app.core.config import settings
from app.core.logger import logger


async def check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def generate(prompt: str, model: str | None = None, system: str | None = None) -> str:
    model = model or settings.LLM_MODEL
    payload = {"model": model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")
    except httpx.ConnectError:
        logger.warning("Ollama not reachable")
        raise ConnectionError("Ollama is not running. Please start Ollama and try again.")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        raise


async def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    model = model or settings.EMBEDDING_MODEL
    results = []
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            for text in texts:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": model, "prompt": text},
                )
                resp.raise_for_status()
                results.append(resp.json().get("embedding", []))
    except httpx.ConnectError:
        raise ConnectionError("Ollama is not running.")
    return results
