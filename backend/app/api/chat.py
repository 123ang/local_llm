import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionOut, ChatMessageOut
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
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
    
    # Get or create session
    if data.session_id:
        session_result = await db.execute(select(ChatSession).where(ChatSession.id == data.session_id, ChatSession.user_id == current_user.id))
        session = session_result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        company_id = data.company_id or current_user.company_id or 0
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
        query_company_id = data.company_id or current_user.company_id
        result = await unified_query(
            question=data.message,
            company_id=query_company_id,
            db=db,
            enabled_sources=data.sources,
        )
        answer = result.get("answer", "I couldn't find an answer to that question.")
        sources = result.get("sources")
        sql_generated = None  # Don't expose raw SQL to users
    except Exception as e:
        answer = f"I'm sorry, I encountered an error processing your question. The LLM service may not be available. Error: {str(e)}"
        sources = None
        sql_generated = None
    
    elapsed = int((time.time() - start) * 1000)
    
    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id, role="assistant", content=answer,
        sources=sources, sql_generated=sql_generated, response_time_ms=elapsed,
    )
    db.add(assistant_msg)
    await db.commit()
    
    return ChatResponse(session_id=session.id, message=answer, sources=sources, sql_generated=sql_generated, response_time_ms=elapsed)

@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
