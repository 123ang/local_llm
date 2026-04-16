import httpx
from app.core.config import settings
from app.core.logger import logger

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=httpx.Timeout(300, connect=10),
        )
    return _client


async def check_ollama() -> bool:
    try:
        resp = await _get_client().get("/api/tags")
        return resp.status_code == 200
    except Exception:
        return False


async def generate(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    max_tokens: int = 512,
    fast: bool = False,
) -> str:
    """Chat-based generation with thinking disabled for speed."""
    model = model or (settings.LLM_MODEL_FAST if fast else settings.LLM_MODEL)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "num_ctx": 4096,
            "num_predict": max_tokens,
            "temperature": 0.3,
        },
    }

    try:
        resp = await _get_client().post("/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")
    except httpx.ConnectError:
        logger.warning("Ollama not reachable")
        raise ConnectionError("Ollama is not running. Please start Ollama and try again.")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        raise


async def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    model = model or settings.EMBEDDING_MODEL
    client = _get_client()
    results = []
    try:
        for text in texts:
            resp = await client.post(
                "/api/embeddings",
                json={"model": model, "prompt": text},
            )
            resp.raise_for_status()
            results.append(resp.json().get("embedding", []))
    except httpx.ConnectError:
        raise ConnectionError("Ollama is not running.")
    return results
