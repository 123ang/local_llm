import fitz  # PyMuPDF
from pathlib import Path
from app.core.logger import logger


def extract_text_from_pdf(file_path: str | Path) -> list[dict]:
    """Extract text from each page of a PDF, returns list of {page, text}."""
    pages = []
    try:
        doc = fitz.open(str(file_path))
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                pages.append({"page": page_num + 1, "text": text.strip()})
        doc.close()
    except Exception as e:
        logger.error(f"PDF parse error for {file_path}: {e}")
        raise
    return pages


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind(". ")
            last_newline = chunk.rfind("\n")
            break_point = max(last_period, last_newline)
            if break_point > chunk_size * 0.5:
                chunk = chunk[: break_point + 1]
                end = start + break_point + 1

        chunks.append(chunk.strip())
        start = end - overlap

    return [c for c in chunks if c]
