import redis.asyncio as aioredis
import shutil
import subprocess
from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine

router = APIRouter(prefix="/status", tags=["status"])


def _gpu_status() -> dict:
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return {
            "available": False,
            "provider": "unavailable",
            "memory_used_mb": None,
            "memory_total_mb": None,
        }
    try:
        result = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        first_gpu = result.stdout.strip().splitlines()[0]
        used, total = [int(part.strip()) for part in first_gpu.split(",", 1)]
        return {
            "available": True,
            "provider": "nvidia",
            "memory_used_mb": used,
            "memory_total_mb": total,
        }
    except Exception:
        return {
            "available": False,
            "provider": "nvidia",
            "memory_used_mb": None,
            "memory_total_mb": None,
        }


@router.get("")
async def get_status():
    """Live health check for all system components."""

    # 1. Ollama
    ollama_ok = False
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
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
        },
        "gpu": _gpu_status(),
        "rag": {
            "connected": bool(ollama_ok and db_ok),
        },
        "database": {
            "connected": db_ok,
            "version": db_version,
        },
        "redis": {
            "connected": redis_ok,
        },
    }
