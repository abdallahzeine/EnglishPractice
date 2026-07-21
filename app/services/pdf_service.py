import re
from pathlib import Path

from pypdf import PdfReader

MIN_PARAGRAPH_CHARS = 80
MAX_PARAGRAPH_CHARS = 1200


def extract_paragraphs(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    paragraphs: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for chunk in re.split(r"\n\s*\n", text):
            cleaned = " ".join(chunk.split())
            if len(cleaned) >= MIN_PARAGRAPH_CHARS:
                paragraphs.extend(_split_long(cleaned))
    return paragraphs


def _split_long(paragraph: str) -> list[str]:
    if len(paragraph) <= MAX_PARAGRAPH_CHARS:
        return [paragraph]
    sentences = re.split(r"(?<=[.!?]) ", paragraph)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) > MAX_PARAGRAPH_CHARS:
            chunks.append(current.strip())
            current = ""
        current += sentence + " "
    if current.strip():
        chunks.append(current.strip())
    return chunks
