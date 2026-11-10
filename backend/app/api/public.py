import re

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..models import AgentProfile, AgentSession, Case, Location, Organization, Subject, new_id
from ..services import channels
from ..services.rulepacks import active_pack
from ..services.summary import case_graph, case_summary

router = APIRouter(prefix="/public", tags=["public"])


class StartSession(BaseModel):
    location_id: str = ""


class CaseLookup(BaseModel):
    code: str
    identifier: str


def find_profile(db: Session, slug: str) -> AgentProfile:
    profile = db.scalars(select(AgentProfile).where(AgentProfile.slug == slug)).first()
    if not profile:
        raise HTTPException(404, "This assistant does not exist")
    return profile


def case_view(db: Session, case: Case) -> dict:
    pack = active_pack(db, case.org_id, case.pack_id)
    return {"summary": case_summary(case, pack), "graph": case_graph(case, pack)}


@router.get("/agents/{slug}")
def agent_info(slug: str, loc: str = "", db: Session = Depends(get_db)):
    profile = find_profile(db, slug)
    location = db.get(Location, loc) if loc else None
    return {
        "name": profile.name,
        "organization": db.get(Organization, profile.org_id).name,
        "greeting": profile.greeting,
        "identifier_label": profile.identifier_label,
        "location": location.label if location else "",
        "phone_number": profile.phone_number,
        "voice_ready": channels.voice_ready(),
    }


@router.post("/agents/{slug}/sessions")
def start_session(slug: str, body: StartSession, db: Session = Depends(get_db)):
    profile = find_profile(db, slug)
    if not channels.voice_ready():
        raise HTTPException(503, "The voice service is not configured yet")
    location = db.get(Location, body.location_id) if body.location_id else None
    session = AgentSession(id=new_id(), org_id=profile.org_id, profile_id=profile.id, channel="web",
                           location=location.label if location else "")
    session.room = f"rc-{session.id}"
    db.add(session)
    db.commit()
    return {
        "session_id": session.id,
        "session_token": session.token,
        "livekit_url": config.LIVEKIT_URL,
        "livekit_token": channels.room_token(session),
    }


@router.get("/sessions/{session_id}")
def session_state(session_id: str, token: str, db: Session = Depends(get_db)):
    session = db.get(AgentSession, session_id)
    if not session or session.token != token:
        raise HTTPException(404, "Session not found")
    subject = db.get(Subject, session.subject_id) if session.subject_id else None
    case = db.get(Case, session.case_id) if session.case_id else None
    return {
        "identified": bool(subject),
        "name": subject.name if subject else "",
        "case": case_view(db, case) if case else None,
    }


@router.post("/cases/lookup")
def lookup_case(body: CaseLookup, db: Session = Depends(get_db)):
    case = db.scalars(select(Case).where(Case.code == body.code.strip().upper())).first()
    clean = lambda text: re.sub(r"[\s-]", "", text).upper()
    if not case or clean(case.subject.identifier) != clean(body.identifier):
        raise HTTPException(404, "No case matches that code and identifier")
    return case_view(db, case)


@router.get("/qr/{location_id}.svg")
def location_qr(location_id: str, db: Session = Depends(get_db)):
    location = db.get(Location, location_id)
    if not location:
        raise HTTPException(404, "Unknown location")
    profile = db.get(AgentProfile, location.profile_id)
    return Response(channels.qr_svg(channels.web_link(profile, location)), media_type="image/svg+xml")
