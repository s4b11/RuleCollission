import json

from sqlalchemy.orm import Session

from ..models import KnowledgeDocument, RuleDraft, StaffUser
from ..rag.ingest import document_text
from . import llm
from .rulepacks import active_row, check, save_version

SECTIONS = ("offices", "documents", "requirements", "alternatives")

FORMAT = """
A proposal is a JSON object with these optional lists:
- "offices": [{"id": "snake_case", "name": "Readable name"}]
- "documents": [{"id": "snake_case", "name": "Readable name", "aliases": ["other_name"]}]
- "requirements": [{"id": "snake_case", "office": "office id", "produces": "document id",
   "prerequisites": "document id" | {"all_of": [...]} | {"any_of": [...]}, "quote": "source sentence"}]
- "alternatives": [{"id": "alt_snake_case", "office": "office id", "produces": "document id",
   "prerequisites": ..., "substitutes": "document id", "in_offices": ["office id"],
   "approval_by": "office id", "description": "plain sentence"}]
A requirement means: this office issues the "produces" document only after the prerequisites exist.
Use "all_of" when every item is needed and "any_of" when one is enough.
Reuse existing ids when the text refers to an existing office or document. Never invent rules the text does not state.
"""

DOCUMENT_PROMPT = (
    "You turn an organisation's policy text into draft rules for staff to review. "
    "You only propose; staff decide.\n" + FORMAT +
    'Reply with JSON: {"proposal": {...}, "summary": "one or two sentences on what you found"}.'
)

CHAT_PROMPT = (
    "You help a staff member describe their office rules in conversation. Ask short questions until a rule is clear: "
    "which office issues which document, what it needs first, and whether all or any of them are needed. "
    "You only propose; staff decide.\n" + FORMAT +
    'Reply with JSON: {"reply": "your message", "proposal": {...} or null}. '
    "Give a proposal only when the staff member has stated at least one complete rule."
)


def catalogue(db: Session, org_id: str, pack_id: str) -> str:
    data = active_row(db, org_id, pack_id).data
    return json.dumps({"offices": data["offices"], "documents": data["documents"]})


def clean(proposal: dict | None) -> dict:
    proposal = proposal or {}
    result = {key: list(proposal.get(key) or []) for key in SECTIONS}
    for requirement in result["requirements"]:
        quote = requirement.pop("quote", None)
        if quote:
            requirement["source"] = {"kind": "approved_rule", "quote": quote}
    return result


def merged(pack_data: dict, proposal: dict) -> dict:
    result = json.loads(json.dumps(pack_data))
    for section in SECTIONS:
        items = {item["id"]: item for item in result.get(section, [])}
        for item in proposal.get(section, []):
            items[item["id"]] = item
        result[section] = list(items.values())
    return result


def problems(db: Session, org_id: str, pack_id: str, proposal: dict) -> list[str]:
    try:
        check(merged(active_row(db, org_id, pack_id).data, proposal))
        return []
    except Exception as error:
        return str(error).splitlines()


def draft_from_document(db: Session, org_id: str, pack_id: str, document: KnowledgeDocument) -> RuleDraft:
    user = f"Existing catalogue: {catalogue(db, org_id, pack_id)}\n\nPolicy text:\n{document_text(db, document)}"
    answer = llm.chat_json(DOCUMENT_PROMPT, [{"role": "user", "content": user}])
    draft = RuleDraft(org_id=org_id, pack_id=pack_id, source="document", source_ref=document.title,
                      proposal=clean(answer.get("proposal")))
    db.add(draft)
    db.flush()
    return draft


def chat(db: Session, org_id: str, pack_id: str, messages: list[dict]) -> tuple[str, RuleDraft | None]:
    system = f"{CHAT_PROMPT}\nExisting catalogue: {catalogue(db, org_id, pack_id)}"
    answer = llm.chat_json(system, messages)
    draft = None
    if answer.get("proposal"):
        draft = RuleDraft(org_id=org_id, pack_id=pack_id, source="chat", source_ref="Rule chat",
                          proposal=clean(answer["proposal"]))
        db.add(draft)
        db.flush()
    return answer.get("reply", ""), draft


def approve(db: Session, draft: RuleDraft, staff: StaffUser, proposal: dict | None = None) -> None:
    if proposal is not None:
        draft.proposal = clean(proposal)
    data = merged(active_row(db, draft.org_id, draft.pack_id).data, draft.proposal)
    save_version(db, draft.org_id, data, staff.email)
    draft.status = "approved"
    draft.reviewed_by = staff.email


def reject(draft: RuleDraft, staff: StaffUser) -> None:
    draft.status = "rejected"
    draft.reviewed_by = staff.email
