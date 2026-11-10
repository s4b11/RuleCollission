from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AgentSession, Case, CaseNote, ReviewRequest, RulePackVersion, StaffUser, Subject, SubjectDocument
from ..security import current_staff
from ..services import cases
from ..services.rulepacks import active_pack
from ..services.summary import case_graph, case_summary, names

router = APIRouter(prefix="/ops", tags=["ops"])


class IssueDocument(BaseModel):
    document: str
    expires_on: date | None = None


class OpenCase(BaseModel):
    pack_id: str
    goal: str


class ReviewAnswer(BaseModel):
    agree: bool
    note: str = ""
    valid_until: date | None = None


class Note(BaseModel):
    text: str


def own(db: Session, model, item_id: str, user: StaffUser):
    item = db.get(model, item_id)
    if not item or item.org_id != user.org_id:
        raise HTTPException(404, "Not found")
    return item


def subject_view(subject: Subject, open_cases: dict) -> dict:
    case = open_cases.get(subject.id)
    return {
        "id": subject.id, "identifier": subject.identifier, "name": subject.name, "category": subject.category,
        "status": subject.status, "details": subject.details,
        "documents": [
            {"id": d.id, "document": d.document, "issued_by": d.issued_by, "issued_on": str(d.issued_on),
             "expires_on": str(d.expires_on) if d.expires_on else ""}
            for d in subject.documents
        ],
        "case": {"id": case.id, "status": case.status, "code": case.code} if case else None,
    }


def latest_cases(db: Session, org_id: str) -> dict:
    rows = db.scalars(select(Case).where(Case.org_id == org_id).order_by(Case.created_at))
    return {case.subject_id: case for case in rows}


def review_view(db: Session, review: ReviewRequest) -> dict:
    case = db.get(Case, review.case_id)
    _, offices = names(active_pack(db, case.org_id, case.pack_id))
    return {
        "office_name": offices.get(review.target_office, review.target_office),
        "id": review.id, "case_id": case.id, "case_code": case.code, "subject": case.subject.name,
        "kind": review.kind, "about": review.about, "office": review.target_office, "question": review.question,
        "status": review.status, "answer": review.answer, "answered_by": review.answered_by,
        "created_at": review.created_at.isoformat(),
    }


@router.get("/overview")
def overview(user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    all_cases = db.scalars(select(Case).where(Case.org_id == user.org_id)).all()
    counts: dict[str, int] = {}
    for case in all_cases:
        counts[case.status] = counts.get(case.status, 0) + 1
    reviews = db.scalars(select(ReviewRequest).where(
        ReviewRequest.org_id == user.org_id, ReviewRequest.status == "open"
    )).all()
    return {
        "subjects": db.query(Subject).filter_by(org_id=user.org_id).count(),
        "cases_by_status": counts,
        "open_reviews": len(reviews),
        "my_reviews": len([r for r in reviews if r.target_office in ("", user.office)]),
        "sessions": db.query(AgentSession).filter_by(org_id=user.org_id).count(),
    }


@router.get("/catalogue")
def catalogue(user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    rows = db.scalars(select(RulePackVersion).where(RulePackVersion.org_id == user.org_id, RulePackVersion.active))
    return [
        {"pack_id": r.pack_id, "name": r.data["name"],
         "documents": [{"id": d["id"], "name": d["name"]} for d in r.data["documents"]],
         "offices": [{"id": o["id"], "name": o["name"]} for o in r.data["offices"]]}
        for r in rows
    ]


@router.get("/subjects")
def list_subjects(user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    open_cases = latest_cases(db, user.org_id)
    subjects = db.scalars(select(Subject).where(Subject.org_id == user.org_id).order_by(Subject.name))
    return [subject_view(s, open_cases) for s in subjects]


@router.get("/subjects/{subject_id}")
def get_subject(subject_id: str, user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    return subject_view(own(db, Subject, subject_id, user), latest_cases(db, user.org_id))


@router.post("/subjects/{subject_id}/documents")
def issue_document(subject_id: str, body: IssueDocument, user: StaffUser = Depends(current_staff),
                   db: Session = Depends(get_db)):
    subject = own(db, Subject, subject_id, user)
    subject.documents.append(SubjectDocument(document=body.document, issued_by=user.email, expires_on=body.expires_on))
    db.flush()
    cases.refresh_subject_cases(db, subject)
    db.commit()
    return subject_view(subject, latest_cases(db, user.org_id))


@router.delete("/subjects/{subject_id}/documents/{document_id}")
def remove_document(subject_id: str, document_id: str, user: StaffUser = Depends(current_staff),
                    db: Session = Depends(get_db)):
    subject = own(db, Subject, subject_id, user)
    subject.documents = [d for d in subject.documents if d.id != document_id]
    db.flush()
    cases.refresh_subject_cases(db, subject)
    db.commit()
    return subject_view(subject, latest_cases(db, user.org_id))


@router.post("/subjects/{subject_id}/cases")
def open_case(subject_id: str, body: OpenCase, user: StaffUser = Depends(current_staff),
              db: Session = Depends(get_db)):
    case = cases.open_case(db, own(db, Subject, subject_id, user), body.pack_id, body.goal)
    db.commit()
    return {"id": case.id}


@router.get("/cases")
def list_cases(user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    rows = db.scalars(select(Case).where(Case.org_id == user.org_id).order_by(Case.updated_at.desc()))
    return [
        {"id": c.id, "code": c.code, "subject": c.subject.name, "identifier": c.subject.identifier,
         "goal": c.goal, "status": c.status, "updated_at": c.updated_at.isoformat(),
         "open_reviews": len([r for r in c.reviews if r.status == "open"])}
        for c in rows
    ]


@router.get("/cases/{case_id}")
def get_case(case_id: str, user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    case = own(db, Case, case_id, user)
    pack = active_pack(db, case.org_id, case.pack_id)
    documents, offices = names(pack)
    sessions = db.scalars(select(AgentSession).where(AgentSession.case_id == case.id).order_by(AgentSession.started_at))
    return {
        "summary": case_summary(case, pack),
        "graph": case_graph(case, pack),
        "subject_id": case.subject_id,
        "reported": [
            {"id": r["id"], "office": offices.get(r["office"], r["office"]),
             "issues": documents.get(r["produces"], r["produces"]),
             "needs_first": r.get("prerequisites"), "quote": (r.get("source") or {}).get("quote", "")}
            for r in case.reported
        ],
        "reviews": [review_view(db, r) for r in sorted(case.reviews, key=lambda r: r.created_at)],
        "decisions": [
            {"kind": d.kind, "target": d.target, "by": d.staff.name, "office": d.staff.office, "note": d.note,
             "valid_until": str(d.valid_until) if d.valid_until else "", "at": d.created_at.isoformat()}
            for d in case.decisions
        ],
        "notes": [{"author": n.author, "text": n.text, "at": n.created_at.isoformat()} for n in case.notes],
        "sessions": [
            {"id": s.id, "channel": s.channel, "started_at": s.started_at.isoformat(),
             "transcript": [{"role": t.role, "text": t.text} for t in s.transcript]}
            for s in sessions
        ],
    }


@router.post("/cases/{case_id}/notes")
def add_note(case_id: str, body: Note, user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    case = own(db, Case, case_id, user)
    case.notes.append(CaseNote(author=user.name, text=body.text))
    db.commit()
    return {"saved": True}


@router.get("/reviews")
def list_reviews(mine: bool = True, user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    query = select(ReviewRequest).where(ReviewRequest.org_id == user.org_id).order_by(ReviewRequest.created_at.desc())
    reviews = [r for r in db.scalars(query) if r.status != "closed"]
    if mine:
        reviews = [r for r in reviews if r.target_office in ("", user.office)]
    return [review_view(db, r) for r in reviews]


@router.post("/reviews/{review_id}/answer")
def answer_review(review_id: str, body: ReviewAnswer, user: StaffUser = Depends(current_staff),
                  db: Session = Depends(get_db)):
    review = own(db, ReviewRequest, review_id, user)
    if review.status != "open":
        raise HTTPException(409, "This question was already answered")
    try:
        cases.answer_review(db, review, user, body.agree, body.note, body.valid_until)
    except PermissionError as error:
        db.rollback()
        raise HTTPException(403, str(error))
    db.commit()
    return review_view(db, review)


@router.get("/sessions")
def list_sessions(user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    rows = db.scalars(select(AgentSession).where(AgentSession.org_id == user.org_id)
                      .order_by(AgentSession.started_at.desc()).limit(50))
    result = []
    for s in rows:
        subject = db.get(Subject, s.subject_id) if s.subject_id else None
        result.append({
            "id": s.id, "channel": s.channel, "location": s.location, "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else "", "subject": subject.name if subject else "",
            "case_id": s.case_id, "transcript": [{"role": t.role, "text": t.text} for t in s.transcript],
        })
    return result
