import re
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.dependencies import ensure_company_access
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionOut, ChatMessageOut
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.services.company_ai_settings_service import get_or_create_company_ai_settings, normalize_allowed_sources

router = APIRouter(prefix="/chat", tags=["chat"])

FOLLOW_UP_PATTERNS = [
    r"\b(it|that|this|those|them|above|previous|earlier|answer)\b",
    r"\b(table|jadual|format|rank|ranking|top|highest|lowest|sort|compare)\b",
    r"\b(tertinggi|terendah|jadual|atas|sebelum|jawapan|banding|susun)\b",
    r"\bwhich one|what about|how about|can you|could you\b",
]


def _looks_like_follow_up(message: str) -> bool:
    text = message.lower().strip()
    if len(text.split()) <= 8:
        return True
    return any(re.search(pattern, text) for pattern in FOLLOW_UP_PATTERNS)


def _compact_message(content: str, max_chars: int = 700) -> str:
    content = re.sub(r"\s+", " ", content or "").strip()
    if len(content) <= max_chars:
        return content
    return content[:max_chars].rstrip() + "…"


def _sanitize_sources_for_user(sources: dict | None, current_user: User) -> dict | None:
    if not sources:
        return sources
    sanitized = dict(sources)
    database = sanitized.get("database")
    if isinstance(database, dict) and current_user.role not in {"admin", "super_admin"}:
        database = dict(database)
        database.pop("sql", None)
        sanitized["database"] = database
    return sanitized


def _has_attached_evidence(sources: dict | None) -> bool:
    if not sources:
        return False
    db_source = sources.get("database")
    return bool(
        sources.get("documents")
        or sources.get("faq")
        or (isinstance(db_source, dict) and db_source.get("row_count", 0) > 0)
    )


def _add_ai_insight_metadata(sources: dict | None, ai_insights: bool, answer: str) -> dict | None:
    if not sources:
        sources = {}
    enriched = dict(sources)
    has_evidence = _has_attached_evidence(enriched)
    insight_marker = bool(
        re.search(r"\b(insight|recommendation|recommended action|next step|why this matters)\s*:", answer or "", re.I)
    )
    enriched["_meta"] = {
        **(enriched.get("_meta") or {}),
        "ai_insights_enabled": bool(ai_insights),
        "ai_insight_contributed": bool(ai_insights and (insight_marker or not has_evidence)),
    }
    return enriched


async def _build_contextual_question(db: AsyncSession, session_id: int, current_message: str) -> str:
    """Attach recent chat context only when the message looks like a follow-up.

    This keeps normal standalone questions clean while allowing requests like
    "make it into table format" or "which sector is highest?" to resolve
    against the previous answer.
    """
    if not _looks_like_follow_up(current_message):
        return current_message

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
    )
    messages = list(reversed(result.scalars().all()))
    previous = [m for m in messages if m.content != current_message]
    if not previous:
        return current_message

    context_lines = []
    for msg in previous[-5:]:
        role = "User" if msg.role == "user" else "Assistant"
        context_lines.append(f"{role}: {_compact_message(msg.content)}")

    return (
        "Recent conversation context for resolving follow-up references only:\n"
        + "\n".join(context_lines)
        + "\n\nCurrent user question:\n"
        + current_message
    )

@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(company_id: int | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if company_id is not None:
        ensure_company_access(current_user, company_id)
    query = select(ChatSession).where(ChatSession.user_id == current_user.id)
    if company_id is not None:
        query = query.where(ChatSession.company_id == company_id)
    result = await db.execute(query.order_by(ChatSession.updated_at.desc()))
    sessions = result.scalars().all()
    out = []
    for s in sessions:
        count_result = await db.execute(select(func.count(ChatMessage.id)).where(ChatMessage.session_id == s.id))
        out.append(ChatSessionOut(id=s.id, title=s.title, created_at=s.created_at, message_count=count_result.scalar() or 0))
    return out

@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
async def get_messages(session_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session_result = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at))
    return list(result.scalars().all())

@router.post("", response_model=ChatResponse)
async def ask_question(data: ChatRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    start = time.time()
    
    requested_company_id = data.company_id or current_user.company_id
    ensure_company_access(current_user, requested_company_id)
    
    # Get or create session
    if data.session_id:
        session_result = await db.execute(select(ChatSession).where(ChatSession.id == data.session_id, ChatSession.user_id == current_user.id))
        session = session_result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        ensure_company_access(current_user, session.company_id)
        if data.company_id is not None and data.company_id != session.company_id:
            raise HTTPException(status_code=400, detail="Session belongs to a different company")
        requested_company_id = session.company_id
    else:
        company_id = requested_company_id or 0
        session = ChatSession(company_id=company_id, user_id=current_user.id, title=data.message[:100])
        db.add(session)
        await db.commit()
        await db.refresh(session)
    
    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=data.message)
    db.add(user_msg)
    await db.commit()
    
    # Call unified query (LLM)
    try:
        from app.llm.unified_query import unified_query
        query_company_id = requested_company_id
        ai_settings = await get_or_create_company_ai_settings(db, query_company_id)
        enabled_sources = normalize_allowed_sources(data.sources, ai_settings.allowed_sources)
        ai_insights = data.ai_insights
        if ai_insights is None:
            ai_insights = not ai_settings.default_source_only
        if ai_insights and not ai_settings.ai_insights_allowed:
            ai_insights = False
        contextual_question = await _build_contextual_question(db, session.id, data.message)
        result = await unified_query(
            question=contextual_question,
            company_id=query_company_id,
            db=db,
            enabled_sources=enabled_sources,
            ai_insights=ai_insights,
            model_mode=data.model_mode,
            document_min_relevance=ai_settings.min_document_relevance,
            require_citations=ai_settings.require_citations,
        )
        answer = result.get("answer", "I couldn't find an answer to that question.")
        sources = _add_ai_insight_metadata(result.get("sources"), ai_insights, answer)
        sources = _sanitize_sources_for_user(sources, current_user)
        model_tier = result.get("model_tier")
        sql_generated = None
    except Exception as e:
        answer = f"I'm sorry, I encountered an error processing your question. The LLM service may not be available. Error: {str(e)}"
        sources = None
        model_tier = None
        sql_generated = None
    
    elapsed = int((time.time() - start) * 1000)
    
    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id, role="assistant", content=answer,
        sources=sources, sql_generated=sql_generated, response_time_ms=elapsed,
    )
    db.add(assistant_msg)
    await db.commit()
    
    return ChatResponse(session_id=session.id, message=answer, sources=sources, sql_generated=sql_generated, response_time_ms=elapsed, model_tier=model_tier)

@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
