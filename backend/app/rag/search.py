from sqlalchemy.orm import Session

from ..models import KnowledgeChunk, KnowledgeDocument
from .embed import embed


def search(db: Session, org_id: str, query: str, limit: int = 4) -> list[dict]:
    [target] = embed([query])
    titles = {d.id: d.title for d in db.query(KnowledgeDocument).filter_by(org_id=org_id)}
    scored = []
    for chunk in db.query(KnowledgeChunk).filter_by(org_id=org_id):
        if len(chunk.embedding) != len(target):
            continue
        score = sum(a * b for a, b in zip(chunk.embedding, target))
        scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {"document": titles.get(c.document_id, ""), "page": c.page, "text": c.text, "score": round(score, 3)}
        for score, c in scored[:limit] if score > 0
    ]
