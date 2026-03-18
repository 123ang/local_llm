import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def get_status():
    """Live health check for all system components."""

    # 1. Ollama
    ollama_ok = False
    ollama_models: list[str] = []
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
                ollama_models = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass

    # 2. Database
    db_ok = False
    db_version = ""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            row = result.scalar()
            db_ok = True
            # Extract short version e.g. "PostgreSQL 16.2"
            if row:
                parts = row.split(" ")
                db_version = f"{parts[0]} {parts[1]}" if len(parts) >= 2 else row[:20]
    except Exception:
        pass

    # 3. Redis
    redis_ok = False
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        await r.ping()
        redis_ok = True
        await r.aclose()
    except Exception:
        pass

    return {
        "ollama": {
            "connected": ollama_ok,
            "models": ollama_models,
            "url": settings.OLLAMA_BASE_URL,
        },
        "database": {
            "connected": db_ok,
            "version": db_version,
        },
        "redis": {
            "connected": redis_ok,
        },
    }
