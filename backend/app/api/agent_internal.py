from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AgentProfile, AgentSession, ToolDefinition, ToolInvocation, TranscriptLine, now
from ..security import agent_only
from ..services.agent_config import session_config
from ..tools import builtin, http_tool

router = APIRouter(prefix="/internal/agent", tags=["agent"], dependencies=[Depends(agent_only)])


class PhoneSession(BaseModel):
    dialed_number: str
    caller: str = ""
    room: str = ""


class ToolCall(BaseModel):
    arguments: dict = {}


class Line(BaseModel):
    role: str
    text: str


def find_session(db: Session, session_id: str) -> AgentSession:
    session = db.get(AgentSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.get("/sessions/{session_id}/config")
def get_config(session_id: str, db: Session = Depends(get_db)):
    return session_config(db, find_session(db, session_id))


@router.post("/phone-sessions")
def start_phone_session(body: PhoneSession, db: Session = Depends(get_db)):
    digits = lambda number: "".join(c for c in number if c.isdigit())
    profiles = db.scalars(select(AgentProfile).where(AgentProfile.phone_number != "")).all()
    profile = next((p for p in profiles if digits(p.phone_number) == digits(body.dialed_number)), None)
    if not profile:
        raise HTTPException(404, "No assistant is linked to this phone number")
    session = AgentSession(org_id=profile.org_id, profile_id=profile.id, channel="phone",
                           room=body.room, caller=body.caller)
    db.add(session)
    db.commit()
    return session_config(db, session)


@router.post("/sessions/{session_id}/tools/{name}")
def invoke_tool(session_id: str, name: str, body: ToolCall, db: Session = Depends(get_db)):
    session = find_session(db, session_id)
    profile = db.get(AgentProfile, session.profile_id)
    custom = db.scalars(select(ToolDefinition).where(
        ToolDefinition.org_id == session.org_id, ToolDefinition.name == name, ToolDefinition.enabled
    )).first()
    if name in builtin.TOOLS and name in profile.enabled_tools:
        result = builtin.run(name, db, session, profile, body.arguments)
    elif custom:
        try:
            result = http_tool.call(custom, body.arguments)
        except Exception as error:
            result = {"error": str(error)}
    else:
        result = {"error": f"Tool '{name}' is not enabled for this assistant"}
    db.add(ToolInvocation(session_id=session.id, tool=name, arguments=body.arguments, result=result))
    db.commit()
    return result


@router.post("/sessions/{session_id}/transcript")
def add_transcript(session_id: str, body: Line, db: Session = Depends(get_db)):
    session = find_session(db, session_id)
    session.transcript.append(TranscriptLine(role=body.role, text=body.text))
    db.commit()
    return {"saved": True}


@router.post("/sessions/{session_id}/end")
def end_session(session_id: str, db: Session = Depends(get_db)):
    find_session(db, session_id).ended_at = now()
    db.commit()
    return {"ended": True}
