import time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin, ensure_company_admin_access
from app.models.evaluation import EvaluationQuestion, EvaluationRun
from app.models.user import User
from app.schemas.evaluation import EvaluationQuestionCreate, EvaluationQuestionOut, EvaluationQuestionUpdate, EvaluationRunOut
from app.services.audit_service import log_action
from app.services.company_ai_settings_service import get_or_create_company_ai_settings, normalize_allowed_sources

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/{company_id}/questions", response_model=list[EvaluationQuestionOut])
async def list_questions(company_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_admin_access(current_user, company_id)
    result = await db.execute(
        select(EvaluationQuestion).where(EvaluationQuestion.company_id == company_id).order_by(EvaluationQuestion.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{company_id}/questions", response_model=EvaluationQuestionOut, status_code=201)
async def create_question(company_id: int, data: EvaluationQuestionCreate, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_admin_access(current_user, company_id)
    q = EvaluationQuestion(
        company_id=company_id,
        question=data.question.strip(),
        expected_keywords=[k.strip() for k in data.expected_keywords if k.strip()],
        expected_source=data.expected_source.strip() if data.expected_source else None,
        sources=data.sources,
        ai_insights=data.ai_insights,
        created_by=current_user.id,
    )
    db.add(q)
    await db.commit()
    await db.refresh(q)
    await log_action(db, "create_evaluation_question", user_id=current_user.id, company_id=company_id, resource_type="evaluation_question", resource_id=q.id)
    return q


@router.patch("/{company_id}/questions/{question_id}", response_model=EvaluationQuestionOut)
async def update_question(company_id: int, question_id: int, data: EvaluationQuestionUpdate, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_admin_access(current_user, company_id)
    result = await db.execute(select(EvaluationQuestion).where(EvaluationQuestion.id == question_id, EvaluationQuestion.company_id == company_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Evaluation question not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "expected_keywords" and value is not None:
            value = [k.strip() for k in value if k.strip()]
        setattr(q, key, value)
    await db.commit()
    await db.refresh(q)
    return q


@router.delete("/{company_id}/questions/{question_id}", status_code=204)
async def delete_question(company_id: int, question_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_admin_access(current_user, company_id)
    result = await db.execute(select(EvaluationQuestion).where(EvaluationQuestion.id == question_id, EvaluationQuestion.company_id == company_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Evaluation question not found")
    await db.delete(q)
    await db.commit()


@router.get("/{company_id}/runs", response_model=list[EvaluationRunOut])
async def list_runs(company_id: int, question_id: int | None = None, limit: int = Query(50, le=200), current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_admin_access(current_user, company_id)
    query = select(EvaluationRun).where(EvaluationRun.company_id == company_id)
    if question_id:
        query = query.where(EvaluationRun.question_id == question_id)
    result = await db.execute(query.order_by(EvaluationRun.created_at.desc()).limit(limit))
    return list(result.scalars().all())


@router.post("/{company_id}/questions/{question_id}/run", response_model=EvaluationRunOut)
async def run_question(company_id: int, question_id: int, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    ensure_company_admin_access(current_user, company_id)
    result = await db.execute(select(EvaluationQuestion).where(EvaluationQuestion.id == question_id, EvaluationQuestion.company_id == company_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Evaluation question not found")

    from app.llm.unified_query import unified_query

    settings = await get_or_create_company_ai_settings(db, company_id)
    enabled_sources = normalize_allowed_sources(q.sources, settings.allowed_sources)
    start = time.time()
    output = await unified_query(
        question=q.question,
        company_id=company_id,
        db=db,
        enabled_sources=enabled_sources,
        ai_insights=q.ai_insights and settings.ai_insights_allowed,
        model_mode="instant",
        document_min_relevance=settings.min_document_relevance,
        require_citations=settings.require_citations,
    )
    latency_ms = int((time.time() - start) * 1000)
    answer = output.get("answer", "")
    answer_l = answer.lower()
    missing = [kw for kw in (q.expected_keywords or []) if kw.lower() not in answer_l]
    source_blob = str(output.get("sources") or {}).lower()
    source_ok = not q.expected_source or q.expected_source.lower() in source_blob or q.expected_source.lower() in answer_l
    passed = not missing and source_ok and "couldn't find" not in answer_l

    run = EvaluationRun(
        question_id=q.id,
        company_id=company_id,
        passed=passed,
        answer=answer,
        sources_used=output.get("sources"),
        missing_keywords=missing,
        latency_ms=latency_ms,
        model_tier=output.get("model_tier"),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run
