from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..engine import analyze
from ..engine import models as em
from ..models import Case, Decision, ReviewRequest, StaffUser, Subject
from .rulepacks import active_pack

DECISION_FOR_REVIEW = {
    "verify_requirement": ("verify_requirement", None),
    "alternative_approval": ("approve_alternative", "refuse_alternative"),
    "alternative_acceptance": ("accept_alternative", None),
    "unconfirmed_equivalence": ("confirm_equivalence", "reject_equivalence"),
}


def held_documents(subject: Subject) -> list[em.HeldDocument]:
    return [em.HeldDocument(document=d.document, expires_on=d.expires_on) for d in subject.documents]


def engine_case(case: Case) -> em.Case:
    decisions = [
        em.Decision(
            id=d.id, case_id=case.id, kind=d.kind, target=d.target, valid_until=d.valid_until,
            by=em.StaffIdentity(staff_id=d.staff.email, role=d.staff.role, office=d.staff.office),
        )
        for d in case.decisions
    ]
    return em.Case(
        id=case.id,
        goal=case.goal,
        as_of=date.today(),
        applicant_category=case.subject.category or None,
        held=held_documents(case.subject),
        reported_requirements=[em.Requirement.model_validate(r) for r in case.reported],
        alias_claims=[em.AliasClaim.model_validate(a) for a in case.alias_claims],
        decisions=decisions,
    )


def case_status(result: em.Analysis) -> str:
    if result.status != em.OutcomeStatus.route_available:
        return result.status.value
    if not result.route.steps:
        return "completed"
    return f"route_{result.route.status.value}"


def sync_reviews(db: Session, case: Case, result: em.Analysis) -> None:
    wanted = {}
    for c in result.clarifications:
        key = f"{case.id}|{c.kind}|{c.about}|{c.target_office or ''}"
        wanted[key] = c
    existing = {r.key: r for r in case.reviews}
    for key, review in existing.items():
        if review.status == "open" and key not in wanted:
            review.status = "closed"
    for key, c in wanted.items():
        if key not in existing:
            case.reviews.append(ReviewRequest(
                org_id=case.org_id, key=key, kind=c.kind, about=c.about,
                target_office=c.target_office or "", question=c.question,
            ))


def analyze_case(db: Session, case: Case) -> em.Analysis:
    pack = active_pack(db, case.org_id, case.pack_id)
    result = analyze(pack, engine_case(case))
    case.analysis = result.model_dump(mode="json")
    case.status = case_status(result)
    sync_reviews(db, case, result)
    db.flush()
    return result


def open_case(db: Session, subject: Subject, pack_id: str, goal: str) -> Case:
    query = select(Case).where(Case.subject_id == subject.id, Case.goal == goal, Case.status != "completed")
    case = db.scalars(query).first()
    if not case:
        case = Case(org_id=subject.org_id, subject_id=subject.id, pack_id=pack_id, goal=goal)
        case.subject = subject
        db.add(case)
        db.flush()
    analyze_case(db, case)
    return case


def refresh_subject_cases(db: Session, subject: Subject) -> None:
    for case in db.scalars(select(Case).where(Case.subject_id == subject.id, Case.status != "completed")):
        analyze_case(db, case)


def record_decision(db: Session, case: Case, staff: StaffUser, kind: str, target: str,
                    valid_until: date | None = None, note: str = "") -> Decision:
    decision = Decision(kind=kind, target=target, staff_id=staff.id, valid_until=valid_until, note=note)
    decision.staff = staff
    case.decisions.append(decision)
    db.flush()
    result = analyze_case(db, case)
    rejected = [n.detail for n in result.notes if n.kind == "rejected_decision" and n.detail.startswith(decision.id)]
    if rejected:
        case.decisions.remove(decision)
        db.flush()
        analyze_case(db, case)
        raise PermissionError(rejected[0].split(": ", 1)[1])
    return decision


def answer_review(db: Session, review: ReviewRequest, staff: StaffUser, agree: bool,
                  note: str = "", valid_until: date | None = None) -> None:
    case = db.get(Case, review.case_id)
    if staff.role not in ("desk_staff", "approver"):
        raise PermissionError("Only staff can answer review requests")
    if review.target_office and staff.office != review.target_office:
        raise PermissionError(f"This question is for the '{review.target_office}' office")

    yes_kind, no_kind = DECISION_FOR_REVIEW.get(review.kind, (None, None))
    target = review.about
    if review.kind == "unconfirmed_equivalence":
        claim = next(a for a in case.alias_claims if a["term"] == review.about)
        target = f"{claim['term']}={claim['document']}"

    review.status = "answered" if agree else "declined"
    review.answer = note
    review.answered_by = staff.email

    if agree and yes_kind:
        record_decision(db, case, staff, yes_kind, target, valid_until, note)
    elif not agree and no_kind:
        record_decision(db, case, staff, no_kind, target, valid_until, note)
    elif not agree and review.kind == "verify_requirement":
        case.reported = [r for r in case.reported if r["id"] != review.about]
        analyze_case(db, case)
    else:
        analyze_case(db, case)
