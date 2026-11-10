import yaml
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..engine.loader import RulePackError
from ..models import (AgentProfile, KnowledgeChunk, KnowledgeDocument, Location, McpServer, RuleDraft,
                      RulePackVersion, StaffUser, ToolDefinition)
from ..rag import ingest
from ..rag.search import search
from ..security import current_admin
from ..services import channels, rule_drafts
from ..services.agent_config import instructions, tool_list
from ..services.llm import LLMUnavailable
from ..services.rulepacks import active_row, save_version
from ..storage import files
from ..tools import http_tool
from ..tools.builtin import TOOLS

router = APIRouter(prefix="/studio", tags=["studio"])

PROFILE_FIELDS = ("name", "prompt", "greeting", "stt_provider", "tts_provider", "voice", "identifier_label",
                  "second_factor_label", "max_attempts", "phone_number", "default_goal", "enabled_tools")


class ProfileUpdate(BaseModel):
    name: str
    prompt: str
    greeting: str
    stt_provider: str
    tts_provider: str
    voice: str
    identifier_label: str
    second_factor_label: str
    max_attempts: int
    phone_number: str
    default_goal: str
    enabled_tools: list[str]


class ToolBody(BaseModel):
    name: str
    description: str
    parameters: dict
    url: str
    method: str = "POST"
    headers: dict = {}
    enabled: bool = True


class McpBody(BaseModel):
    name: str
    url: str
    headers: dict = {}
    enabled: bool = True


class LocationBody(BaseModel):
    label: str


class RulePackBody(BaseModel):
    yaml_text: str


class DraftFromDocument(BaseModel):
    document_id: str


class RuleChat(BaseModel):
    messages: list[dict]


class DraftReview(BaseModel):
    proposal: dict | None = None


class SearchBody(BaseModel):
    query: str


def own(db: Session, model, item_id: str, user: StaffUser):
    item = db.get(model, item_id)
    if not item or item.org_id != user.org_id:
        raise HTTPException(404, "Not found")
    return item


def profile_view(profile: AgentProfile) -> dict:
    view = {field: getattr(profile, field) for field in PROFILE_FIELDS}
    return {**view, "id": profile.id, "slug": profile.slug, "pack_id": profile.pack_id,
            "web_link": channels.web_link(profile)}


def draft_view(db: Session, draft: RuleDraft) -> dict:
    return {
        "id": draft.id, "source": draft.source, "source_ref": draft.source_ref, "status": draft.status,
        "proposal": draft.proposal, "reviewed_by": draft.reviewed_by, "created_at": draft.created_at.isoformat(),
        "problems": rule_drafts.problems(db, draft.org_id, draft.pack_id, draft.proposal)
        if draft.status == "pending" else [],
    }


# ---- agent profile ----

@router.get("/profiles")
def list_profiles(user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    return [profile_view(p) for p in db.query(AgentProfile).filter_by(org_id=user.org_id)]


@router.put("/profiles/{profile_id}")
def update_profile(profile_id: str, body: ProfileUpdate, user: StaffUser = Depends(current_admin),
                   db: Session = Depends(get_db)):
    profile = own(db, AgentProfile, profile_id, user)
    for field in PROFILE_FIELDS:
        setattr(profile, field, getattr(body, field))
    db.commit()
    return profile_view(profile)


@router.get("/profiles/{profile_id}/preview")
def preview(profile_id: str, channel: str = "web", user: StaffUser = Depends(current_admin),
            db: Session = Depends(get_db)):
    profile = own(db, AgentProfile, profile_id, user)
    servers = db.query(McpServer).filter_by(org_id=user.org_id, enabled=True)
    return {
        "instructions": instructions(db, profile, channel, ""),
        "tools": tool_list(db, profile),
        "mcp_servers": [s.name for s in servers],
    }


# ---- tools and MCP ----

@router.get("/tools")
def list_tools(user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    builtin = [{"name": t["name"], "description": t["description"]} for t in TOOLS.values()]
    custom = [
        {"id": t.id, "name": t.name, "description": t.description, "parameters": t.parameters, "url": t.url,
         "method": t.method, "headers": t.headers, "enabled": t.enabled}
        for t in db.query(ToolDefinition).filter_by(org_id=user.org_id)
    ]
    return {"builtin": builtin, "custom": custom}


@router.post("/tools")
def save_tool(body: ToolBody, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    if body.name in TOOLS:
        raise HTTPException(422, "That name is used by a built-in tool")
    try:
        http_tool.check_url(body.url)
    except Exception as error:
        raise HTTPException(422, str(error))
    tool = db.scalars(select(ToolDefinition).where(
        ToolDefinition.org_id == user.org_id, ToolDefinition.name == body.name
    )).first()
    if not tool:
        tool = ToolDefinition(org_id=user.org_id, name=body.name)
        db.add(tool)
    for field, value in body.model_dump().items():
        setattr(tool, field, value)
    db.commit()
    return {"id": tool.id}


@router.delete("/tools/{tool_id}")
def delete_tool(tool_id: str, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    db.delete(own(db, ToolDefinition, tool_id, user))
    db.commit()
    return {"deleted": True}


@router.get("/mcp-servers")
def list_mcp(user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    return [{"id": s.id, "name": s.name, "url": s.url, "headers": s.headers, "enabled": s.enabled}
            for s in db.query(McpServer).filter_by(org_id=user.org_id)]


@router.post("/mcp-servers")
def add_mcp(body: McpBody, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    try:
        http_tool.check_url(body.url)
    except Exception as error:
        raise HTTPException(422, str(error))
    server = McpServer(org_id=user.org_id, **body.model_dump())
    db.add(server)
    db.commit()
    return {"id": server.id}


@router.delete("/mcp-servers/{server_id}")
def delete_mcp(server_id: str, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    db.delete(own(db, McpServer, server_id, user))
    db.commit()
    return {"deleted": True}


# ---- channels ----

@router.get("/profiles/{profile_id}/locations")
def list_locations(profile_id: str, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    profile = own(db, AgentProfile, profile_id, user)
    return [{"id": l.id, "label": l.label, "link": channels.web_link(profile, l)}
            for l in db.query(Location).filter_by(profile_id=profile.id)]


@router.post("/profiles/{profile_id}/locations")
def add_location(profile_id: str, body: LocationBody, user: StaffUser = Depends(current_admin),
                 db: Session = Depends(get_db)):
    profile = own(db, AgentProfile, profile_id, user)
    location = Location(org_id=user.org_id, profile_id=profile.id, label=body.label)
    db.add(location)
    db.commit()
    return {"id": location.id}


@router.delete("/locations/{location_id}")
def delete_location(location_id: str, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    db.delete(own(db, Location, location_id, user))
    db.commit()
    return {"deleted": True}


# ---- knowledge ----

@router.get("/knowledge")
def list_knowledge(user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    return [{"id": d.id, "title": d.title, "filename": d.filename, "chunks": d.chunk_count,
             "created_at": d.created_at.isoformat()}
            for d in db.query(KnowledgeDocument).filter_by(org_id=user.org_id)]


@router.post("/knowledge")
def upload_knowledge(title: str = Form(...), file: UploadFile = File(...),
                     user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    document = ingest.add_document(db, user.org_id, title, file.filename, file.file.read())
    db.commit()
    return {"id": document.id, "chunks": document.chunk_count}


@router.delete("/knowledge/{document_id}")
def delete_knowledge(document_id: str, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    document = own(db, KnowledgeDocument, document_id, user)
    db.query(KnowledgeChunk).filter_by(document_id=document.id).delete()
    files.delete(document.storage_key)
    db.delete(document)
    db.commit()
    return {"deleted": True}


@router.post("/knowledge/search")
def test_search(body: SearchBody, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    return search(db, user.org_id, body.query)


# ---- rule packs and drafts ----

@router.get("/rulepacks/{pack_id}")
def get_rulepack(pack_id: str, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    row = active_row(db, user.org_id, pack_id)
    if not row:
        raise HTTPException(404, "Rule pack not found")
    versions = db.scalars(select(RulePackVersion).where(
        RulePackVersion.org_id == user.org_id, RulePackVersion.pack_id == pack_id
    ).order_by(RulePackVersion.version.desc()))
    return {
        "data": row.data,
        "yaml_text": yaml.safe_dump(row.data, sort_keys=False),
        "versions": [{"version": v.version, "active": v.active, "created_by": v.created_by,
                      "created_at": v.created_at.isoformat()} for v in versions],
    }


@router.put("/rulepacks/{pack_id}")
def replace_rulepack(pack_id: str, body: RulePackBody, user: StaffUser = Depends(current_admin),
                     db: Session = Depends(get_db)):
    try:
        data = yaml.safe_load(body.yaml_text)
        if not isinstance(data, dict) or data.get("pack_id") != pack_id:
            raise RulePackError("The file must keep the same pack_id")
        row = save_version(db, user.org_id, data, user.email)
    except (RulePackError, yaml.YAMLError) as error:
        db.rollback()
        raise HTTPException(422, str(error))
    db.commit()
    return {"version": row.version}


@router.get("/rulepacks/{pack_id}/drafts")
def list_drafts(pack_id: str, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    drafts = db.scalars(select(RuleDraft).where(
        RuleDraft.org_id == user.org_id, RuleDraft.pack_id == pack_id
    ).order_by(RuleDraft.created_at.desc()))
    return [draft_view(db, d) for d in drafts]


@router.post("/rulepacks/{pack_id}/drafts/from-document")
def draft_from_document(pack_id: str, body: DraftFromDocument, user: StaffUser = Depends(current_admin),
                        db: Session = Depends(get_db)):
    document = own(db, KnowledgeDocument, body.document_id, user)
    try:
        draft = rule_drafts.draft_from_document(db, user.org_id, pack_id, document)
    except LLMUnavailable as error:
        raise HTTPException(503, f"The language model is not available: {error}")
    db.commit()
    return draft_view(db, draft)


@router.post("/rulepacks/{pack_id}/drafts/chat")
def rule_chat(pack_id: str, body: RuleChat, user: StaffUser = Depends(current_admin),
              db: Session = Depends(get_db)):
    try:
        reply, draft = rule_drafts.chat(db, user.org_id, pack_id, body.messages)
    except LLMUnavailable as error:
        raise HTTPException(503, f"The language model is not available: {error}")
    db.commit()
    return {"reply": reply, "draft": draft_view(db, draft) if draft else None}


@router.post("/drafts/{draft_id}/approve")
def approve_draft(draft_id: str, body: DraftReview, user: StaffUser = Depends(current_admin),
                  db: Session = Depends(get_db)):
    draft = own(db, RuleDraft, draft_id, user)
    if draft.status != "pending":
        raise HTTPException(409, "This draft was already reviewed")
    try:
        rule_drafts.approve(db, draft, user, body.proposal)
    except Exception as error:
        db.rollback()
        raise HTTPException(422, str(error))
    db.commit()
    return draft_view(db, draft)


@router.post("/drafts/{draft_id}/reject")
def reject_draft(draft_id: str, user: StaffUser = Depends(current_admin), db: Session = Depends(get_db)):
    draft = own(db, RuleDraft, draft_id, user)
    rule_drafts.reject(draft, user)
    db.commit()
    return draft_view(db, draft)
