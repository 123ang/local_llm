from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin, ensure_company_admin_access
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _has_source(sources: dict | None, name: str) -> bool:
    if not sources:
        return False
    val = sources.get(name)
    if isinstance(val, list):
        return len(val) > 0
    return bool(val)


@router.get("/{company_id}/summary")
async def analytics_summary(company_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_admin_access(current_user, company_id)
    since = datetime.now(timezone.utc) - timedelta(days=30)

    total_questions = await db.scalar(
        select(func.count(ChatMessage.id))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.company_id == company_id, ChatMessage.role == "user", ChatMessage.created_at >= since)
    ) or 0
    assistant_result = await db.execute(
        select(ChatMessage)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.company_id == company_id, ChatMessage.role == "assistant", ChatMessage.created_at >= since)
        .order_by(ChatMessage.created_at.desc())
        .limit(500)
    )
    assistant_messages = list(assistant_result.scalars().all())
    refused = [m for m in assistant_messages if "couldn't find" in (m.content or "").lower() or "source-only mode" in (m.content or "").lower()]
    latencies = [m.response_time_ms for m in assistant_messages if m.response_time_ms is not None]

    source_counts = {"database": 0, "documents": 0, "faq": 0}
    doc_counts: dict[str, int] = {}
    dataset_counts: dict[str, int] = {}
    for msg in assistant_messages:
        sources = msg.sources or {}
        for key in source_counts:
            if _has_source(sources, key):
                source_counts[key] += 1
        for doc in sources.get("documents") or []:
            name = doc.get("source") or "Unknown document"
            doc_counts[name] = doc_counts.get(name, 0) + 1
        db_source = sources.get("database") or {}
        for name in db_source.get("datasets") or db_source.get("tables") or []:
            dataset_counts[name] = dataset_counts.get(name, 0) + 1

    user_q_result = await db.execute(
        select(ChatMessage.content, func.count(ChatMessage.id).label("count"))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.company_id == company_id, ChatMessage.role == "user", ChatMessage.created_at >= since)
        .group_by(ChatMessage.content)
        .order_by(func.count(ChatMessage.id).desc())
        .limit(10)
    )

    active_users = await db.scalar(
        select(func.count(func.distinct(ChatSession.user_id))).where(ChatSession.company_id == company_id, ChatSession.updated_at >= since)
    ) or 0

    return {
        "window_days": 30,
        "total_questions": total_questions,
        "assistant_answers": len(assistant_messages),
        "refused_or_unanswered": len(refused),
        "active_users": active_users,
        "average_response_time_ms": round(sum(latencies) / len(latencies)) if latencies else None,
        "source_counts": source_counts,
        "top_questions": [{"question": row.content, "count": row.count} for row in user_q_result.all()],
        "top_documents": sorted([{"name": k, "count": v} for k, v in doc_counts.items()], key=lambda x: x["count"], reverse=True)[:10],
        "top_datasets": sorted([{"name": k, "count": v} for k, v in dataset_counts.items()], key=lambda x: x["count"], reverse=True)[:10],
    }
