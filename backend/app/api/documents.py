import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import (
    require_knowledge_admin,
    ensure_company_access,
    ensure_department_access,
    resolve_department_scope,
)
from app.core.security import get_current_user
from app.core.config import settings
from app.schemas.document import DocumentOut
from app.models.document import Document
from app.models.user import User
from app.services.audit_service import log_action
from app.ingestion.pdf_processor import process_document
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["documents"])

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED_TYPES = {PDF_MIME, DOCX_MIME}
ALLOWED_SUFFIXES = {".pdf": PDF_MIME, ".docx": DOCX_MIME}


@router.get("/{company_id}", response_model=list[DocumentOut])
async def list_documents(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ensure_company_access(current_user, company_id)
    department_ids = await resolve_department_scope(db, current_user, company_id)
    if not department_ids:
        return []
    result = await db.execute(
        select(Document)
        .where(Document.company_id == company_id, Document.department_id.in_(department_ids))
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{company_id}", response_model=DocumentOut, status_code=201)
async def upload_document(
    company_id: int,
    background_tasks: BackgroundTasks,
    department_id: int = Form(...),
    visibility: str = Form("department"),
    file: UploadFile = File(...),
    current_user: User = Depends(require_knowledge_admin),
    db: AsyncSession = Depends(get_db),
):
    ensure_company_access(current_user, company_id)
    await ensure_department_access(db, current_user, company_id, department_id)
    original_name = Path(file.filename or "upload").name
    suffix = Path(original_name).suffix.lower()
    mime_type = file.content_type if file.content_type in ALLOWED_TYPES else ALLOWED_SUFFIXES.get(suffix)
    if mime_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF or Word .docx files are allowed")

    company_dir = Path(settings.UPLOAD_DIR) / "companies" / str(company_id) / "documents"
    company_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = company_dir / safe_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        company_id=company_id,
        department_id=department_id,
        visibility=visibility,
        filename=safe_name,
        original_name=original_name,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=mime_type,
        status="pending",
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    await log_action(
        db, action="upload_document", user_id=current_user.id,
        company_id=company_id, resource_type="document", resource_id=doc.id,
    )

    # Trigger background processing: parse → chunk → embed → store
    background_tasks.add_task(process_document, doc.id)

    return doc


@router.post("/{company_id}/{document_id}/reprocess", response_model=DocumentOut)
async def reprocess_document(
    company_id: int,
    document_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_knowledge_admin),
    db: AsyncSession = Depends(get_db),
):
    """Re-trigger processing for a document (useful if Ollama was offline during upload)."""
    ensure_company_access(current_user, company_id)
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.company_id == company_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await ensure_department_access(db, current_user, company_id, doc.department_id)

    doc.status = "pending"
    doc.error_message = None
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(process_document, doc.id)
    return doc


@router.delete("/{company_id}/{document_id}", status_code=204)
async def delete_document(
    company_id: int,
    document_id: int,
    current_user: User = Depends(require_knowledge_admin),
    db: AsyncSession = Depends(get_db),
):
    ensure_company_access(current_user, company_id)
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.company_id == company_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await ensure_department_access(db, current_user, company_id, doc.department_id)
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await db.delete(doc)
    await db.commit()


@router.get("/{company_id}/{document_id}/file")
async def view_document_file(
    company_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ensure_company_access(current_user, company_id)
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.company_id == company_id)
    )
    doc = result.scalar_one_or_none()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    await ensure_department_access(db, current_user, company_id, doc.department_id)
    return FileResponse(doc.file_path, media_type=doc.mime_type or "application/pdf", filename=doc.original_name)
