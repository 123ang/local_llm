from pathlib import Path
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET


WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_text_from_docx(path: str | Path) -> list[dict]:
    """Extract paragraph text from a .docx file using only the OOXML zip payload."""
    try:
        with ZipFile(path) as docx:
            document_xml = docx.read("word/document.xml")
    except (BadZipFile, KeyError, OSError):
        return []

    try:
        root = ET.fromstring(document_xml)
    except ET.ParseError:
        return []

    paragraphs: list[str] = []
    for paragraph in root.iter(f"{WORD_NAMESPACE}p"):
        text_parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{WORD_NAMESPACE}t" and node.text:
                text_parts.append(node.text)
            elif node.tag == f"{WORD_NAMESPACE}tab":
                text_parts.append("\t")
            elif node.tag == f"{WORD_NAMESPACE}br":
                text_parts.append("\n")
        text = "".join(text_parts).strip()
        if text:
            paragraphs.append(text)

    text = "\n".join(paragraphs).strip()
    return [{"page": 1, "text": text}] if text else []
