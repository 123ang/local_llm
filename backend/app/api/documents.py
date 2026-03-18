import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.security import get_current_user
from app.core.config import settings
from app.schemas.document import DocumentOut
from app.models.document import Document
from app.models.user import User
from app.services.audit_service import log_action
from app.ingestion.pdf_processor import process_document
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {"application/pdf"}


@router.get("/{company_id}", response_model=list[DocumentOut])
async def list_documents(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.company_id == company_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{company_id}", response_model=DocumentOut, status_code=201)
async def upload_document(
    company_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    company_dir = Path(settings.UPLOAD_DIR) / "companies" / str(company_id) / "pdf"
    company_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = company_dir / safe_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        company_id=company_id,
        filename=safe_name,
        original_name=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
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
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Re-trigger processing for a document (useful if Ollama was offline during upload)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.company_id == company_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

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
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.company_id == company_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await db.delete(doc)
    await db.commit()
