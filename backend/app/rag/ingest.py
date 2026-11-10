import io

from pypdf import PdfReader
from sqlalchemy.orm import Session

from ..models import KnowledgeChunk, KnowledgeDocument, new_id
from ..storage import files
from .embed import embed

CHUNK_SIZE = 800


def read_pages(filename: str, content: bytes) -> list[str]:
    if filename.lower().endswith(".pdf"):
        return [page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages]
    return [content.decode("utf-8", errors="ignore")]


def split(text: str) -> list[str]:
    chunks, current = [], ""
    for paragraph in text.split("\n\n"):
        paragraph = " ".join(paragraph.split())
        if not paragraph:
            continue
        if current and len(current) + len(paragraph) > CHUNK_SIZE:
            chunks.append(current)
            current = ""
        current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


def add_document(db: Session, org_id: str, title: str, filename: str, content: bytes) -> KnowledgeDocument:
    document = KnowledgeDocument(id=new_id(), org_id=org_id, title=title, filename=filename, storage_key="")
    document.storage_key = f"knowledge/{org_id}/{document.id}/{filename}"
    files.save(document.storage_key, content)
    db.add(document)
    db.flush()

    pieces = [(number, chunk) for number, page in enumerate(read_pages(filename, content), 1) for chunk in split(page)]
    vectors = embed([text for _, text in pieces]) if pieces else []
    for (page, text), vector in zip(pieces, vectors):
        db.add(KnowledgeChunk(org_id=org_id, document_id=document.id, page=page, text=text, embedding=vector))
    document.chunk_count = len(pieces)
    db.flush()
    return document


def document_text(db: Session, document: KnowledgeDocument, limit: int = 12000) -> str:
    chunks = db.query(KnowledgeChunk).filter_by(document_id=document.id).order_by(KnowledgeChunk.page).all()
    return "\n\n".join(c.text for c in chunks)[:limit]
