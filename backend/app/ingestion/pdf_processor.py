"""
Full PDF processing pipeline:
  1. Extract text per page (PyMuPDF)
  2. Split into overlapping chunks
  3. Generate embeddings for each chunk (Ollama nomic-embed-text)
  4. Save DocumentChunk rows with content + embedding
  5. Update Document status to 'ready'
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import async_session
from app.core.logger import logger
from app.models.document import Document, DocumentChunk
from app.ingestion.pdf_parser import extract_text_from_pdf, chunk_text
from app.llm.embeddings.embedding_client import get_embedding


async def process_document(document_id: int) -> None:
    """
    Entry point for background processing. Opens its own DB session
    so it can be called from FastAPI BackgroundTasks.
    """
    async with async_session() as db:
        await _run_pipeline(document_id, db)


async def _run_pipeline(document_id: int, db: AsyncSession) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        logger.warning(f"Document {document_id} not found for processing")
        return

    logger.info(f"Processing document {document_id}: {doc.original_name}")

    # Mark as processing
    doc.status = "processing"
    await db.commit()

    try:
        # 1. Extract text pages
        pages = extract_text_from_pdf(doc.file_path)
        if not pages:
            doc.status = "error"
            doc.error_message = "No text could be extracted from this PDF."
            await db.commit()
            return

        doc.page_count = len(pages)

        # 2. Chunk text and generate embeddings
        all_chunks: list[dict] = []
        for page_data in pages:
            page_chunks = chunk_text(page_data["text"], chunk_size=800, overlap=150)
            for chunk_text_content in page_chunks:
                if chunk_text_content.strip():
                    all_chunks.append({
                        "content": chunk_text_content.strip(),
                        "page": page_data["page"],
                    })

        if not all_chunks:
            doc.status = "error"
            doc.error_message = "No text chunks found after processing."
            await db.commit()
            return

        logger.info(f"Document {document_id}: {len(all_chunks)} chunks to embed")

        # 3. Delete existing chunks (in case of reprocessing)
        existing = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        for old_chunk in existing.scalars().all():
            await db.delete(old_chunk)
        await db.commit()

        # 4. Embed and save each chunk
        chunk_objs = []
        for idx, chunk_data in enumerate(all_chunks):
            try:
                embedding = await get_embedding(chunk_data["content"])
            except ConnectionError:
                logger.warning(f"Ollama not available — saving chunk {idx} without embedding")
                embedding = None

            chunk_obj = DocumentChunk(
                document_id=document_id,
                company_id=doc.company_id,
                chunk_index=idx,
                content=chunk_data["content"],
                page_number=chunk_data["page"],
                embedding=embedding,
            )
            db.add(chunk_obj)
            chunk_objs.append(chunk_obj)

            # Commit every 20 chunks to avoid large transactions
            if (idx + 1) % 20 == 0:
                await db.commit()
                logger.info(f"Document {document_id}: saved {idx + 1}/{len(all_chunks)} chunks")

        await db.commit()

        # 5. Update document status
        doc.chunk_count = len(chunk_objs)
        doc.status = "ready"
        doc.error_message = None
        await db.commit()

        logger.info(f"Document {document_id} processed: {len(chunk_objs)} chunks, {doc.page_count} pages")

    except Exception as e:
        logger.error(f"Document {document_id} processing failed: {e}", exc_info=True)
        doc.status = "error"
        doc.error_message = str(e)
        await db.commit()
