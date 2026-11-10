"""Tools the voice agent can call. They read records, propose and take notes.
None of them can record a staff decision."""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AgentProfile, AgentSession, Case, CaseNote, Subject, new_id
from ..rag.search import search
from ..services import cases
from ..services.rulepacks import active_pack
from ..services.summary import case_summary

TOOLS: dict[str, dict] = {}


def tool(name: str, description: str, properties: dict | None = None, required: list[str] | None = None):
    def register(handler):
        TOOLS[name] = {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties or {}, "required": required or []},
            "handler": handler,
        }
        return handler
    return register


class ToolError(Exception):
    pass


def current_case(db: Session, session: AgentSession) -> Case:
    if not session.subject_id:
        raise ToolError("The person is not identified yet. Ask for their identifier and call identify_subject first.")
    if not session.case_id:
        raise ToolError("No case is open. Ask what they are trying to obtain, then call open_case.")
    return db.get(Case, session.case_id)


def summary(db: Session, case: Case) -> dict:
    return case_summary(case, active_pack(db, case.org_id, case.pack_id))


@tool("identify_subject", "Match the person to their record using the configured identifier.",
      {"identifier": {"type": "string"}, "second_factor": {"type": "string"}}, ["identifier"])
def identify_subject(db, session, profile, args):
    if session.failed_attempts >= profile.max_attempts:
        return {"identified": False, "message": "Too many failed attempts. Please ask the person to visit the help desk."}
    identifier = re.sub(r"[\s-]", "", str(args["identifier"])).upper()
    query = select(Subject).where(Subject.org_id == session.org_id)
    subject = next((s for s in db.scalars(query) if re.sub(r"[\s-]", "", s.identifier).upper() == identifier), None)
    second = str(args.get("second_factor", "")).strip()
    if profile.second_factor_label and subject and not second:
        return {"identified": False, "message": f"Also ask for their {profile.second_factor_label}."}
    if not subject or (profile.second_factor_label and subject.second_factor != second):
        session.failed_attempts += 1
        return {"identified": False, "attempts_left": profile.max_attempts - session.failed_attempts}
    session.subject_id = subject.id
    result = {"identified": True, "name": subject.name}
    if profile.default_goal:
        case = cases.open_case(db, subject, profile.pack_id, profile.default_goal)
        session.case_id = case.id
        result["case"] = summary(db, case)
    return result


@tool("open_case", "Open a case for the document the person is trying to obtain.",
      {"goal_document": {"type": "string", "description": "Document id from the catalogue"}}, ["goal_document"])
def open_case(db, session, profile, args):
    if not session.subject_id:
        raise ToolError("Identify the person first.")
    pack = active_pack(db, session.org_id, profile.pack_id)
    if args["goal_document"] not in {d.id for d in pack.documents}:
        raise ToolError("Unknown document id. Call lookup_rules to see the catalogue.")
    case = cases.open_case(db, db.get(Subject, session.subject_id), profile.pack_id, args["goal_document"])
    session.case_id = case.id
    return summary(db, case)


@tool("get_case_status", "Recompute and return the route, blockers and open questions for the current case.")
def get_case_status(db, session, profile, args):
    case = current_case(db, session)
    cases.analyze_case(db, case)
    return summary(db, case)


@tool("lookup_rules", "List the organisation's approved offices, documents and rules.",
      {"document": {"type": "string", "description": "Optional document id to filter by"}})
def lookup_rules(db, session, profile, args):
    pack = active_pack(db, session.org_id, profile.pack_id)
    wanted = args.get("document")
    rules = [
        {"id": r.id, "office": r.office, "issues": r.produces, "needs_first": r.prerequisites}
        for r in pack.requirements if not wanted or r.produces == wanted
    ]
    return {
        "offices": [o.model_dump() for o in pack.offices],
        "documents": [d.model_dump() for d in pack.documents],
        "rules": rules,
    }


@tool("propose_requirement",
      "Record what the person says an office told them. It stays unverified until that office confirms it.",
      {
          "office": {"type": "string", "description": "Office id"},
          "issues": {"type": "string", "description": "Document id the office issues"},
          "needs_first": {"type": "array", "items": {"type": "string"}, "description": "Document ids or the exact words used"},
          "needs_all": {"type": "boolean", "description": "True if every item is needed, false if any one is enough"},
          "quote": {"type": "string", "description": "The person's own words"},
      }, ["office", "issues", "needs_first", "quote"])
def propose_requirement(db, session, profile, args):
    case = current_case(db, session)
    pack = active_pack(db, case.org_id, case.pack_id)
    if args["office"] not in {o.id for o in pack.offices}:
        raise ToolError("Unknown office id. Call lookup_rules to see the catalogue.")
    if args["issues"] not in {d.id for d in pack.documents}:
        raise ToolError("Unknown document id. Call lookup_rules to see the catalogue.")
    key = "all_of" if args.get("needs_all", True) else "any_of"
    requirement = {
        "id": f"rep_{new_id()}",
        "office": args["office"],
        "produces": args["issues"],
        "prerequisites": {key: list(args["needs_first"])},
        "source": {"kind": "applicant_report", "quote": args["quote"]},
    }
    same = lambda r: r["office"] == args["office"] and r["produces"] == args["issues"]
    case.reported = [r for r in case.reported if not same(r)] + [requirement]
    cases.analyze_case(db, case)
    return summary(db, case)


@tool("propose_equivalence",
      "Record that an office may be using a different name for a known document. The office must confirm it.",
      {"term": {"type": "string"}, "document": {"type": "string", "description": "Known document id"},
       "office": {"type": "string", "description": "Office id that used the term"}}, ["term", "document", "office"])
def propose_equivalence(db, session, profile, args):
    case = current_case(db, session)
    claim = {"term": args["term"], "document": args["document"], "office": args["office"]}
    case.alias_claims = [a for a in case.alias_claims if a["term"] != args["term"]] + [claim]
    cases.analyze_case(db, case)
    return summary(db, case)


@tool("list_open_questions", "List the questions waiting for staff, with the office that must answer each.")
def list_open_questions(db, session, profile, args):
    case = current_case(db, session)
    return {"questions": summary(db, case)["questions"]}


@tool("get_documents_on_file", "List the documents the organisation's records show for this person.")
def get_documents_on_file(db, session, profile, args):
    case = current_case(db, session)
    return {"documents": [
        {"document": d.document, "issued_on": str(d.issued_on), "expires_on": str(d.expires_on or "")}
        for d in case.subject.documents
    ]}


@tool("add_case_note", "Write a short note on the case for staff to read.", {"text": {"type": "string"}}, ["text"])
def add_case_note(db, session, profile, args):
    case = current_case(db, session)
    case.notes.append(CaseNote(author=f"agent ({session.channel})", text=str(args["text"])[:1000]))
    return {"saved": True}


@tool("search_knowledge", "Search the organisation's uploaded policy documents and return passages to quote.",
      {"query": {"type": "string"}}, ["query"])
def search_knowledge(db, session, profile, args):
    return {"passages": search(db, session.org_id, args["query"])}


def run(name: str, db: Session, session: AgentSession, profile: AgentProfile, args: dict) -> dict:
    try:
        return TOOLS[name]["handler"](db, session, profile, args)
    except ToolError as error:
        return {"error": str(error)}
    except KeyError as error:
        return {"error": f"Missing argument: {error}"}
