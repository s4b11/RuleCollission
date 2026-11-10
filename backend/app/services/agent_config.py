from sqlalchemy.orm import Session

from .. import config
from ..models import AgentProfile, AgentSession, McpServer, Organization, ToolDefinition
from ..tools.builtin import TOOLS
from .rulepacks import active_row


def tool_list(db: Session, profile: AgentProfile) -> list[dict]:
    builtin = [
        {key: TOOLS[name][key] for key in ("name", "description", "parameters")}
        for name in profile.enabled_tools if name in TOOLS
    ]
    custom = [
        {"name": t.name, "description": t.description, "parameters": t.parameters}
        for t in db.query(ToolDefinition).filter_by(org_id=profile.org_id, enabled=True)
    ]
    return builtin + custom


def instructions(db: Session, profile: AgentProfile, channel: str, location: str) -> str:
    org = db.get(Organization, profile.org_id)
    pack = active_row(db, profile.org_id, profile.pack_id).data
    offices = ", ".join(f"{o['id']} ({o['name']})" for o in pack["offices"])
    documents = ", ".join(f"{d['id']} ({d['name']})" for d in pack["documents"])
    parts = [
        f"You are the assistant of {org.name}.",
        profile.prompt,
        f"Identify the person by their {profile.identifier_label} before discussing any case."
        + (f" Also ask for their {profile.second_factor_label}." if profile.second_factor_label else ""),
        f"Offices: {offices}.",
        f"Documents: {documents}.",
    ]
    if location:
        parts.append(f"The person scanned the code at: {location}.")
    if channel == "phone":
        minutes = config.PHONE_SESSION_SECONDS // 60
        parts.append(
            f"This is a phone call limited to {minutes} minutes. Use short sentences. Give the case code at the end "
            "so the caller can open the full route on the web app."
        )
    return "\n".join(p for p in parts if p)


def session_config(db: Session, session: AgentSession) -> dict:
    profile = db.get(AgentProfile, session.profile_id)
    servers = db.query(McpServer).filter_by(org_id=profile.org_id, enabled=True)
    return {
        "session_id": session.id,
        "channel": session.channel,
        "max_seconds": config.PHONE_SESSION_SECONDS if session.channel == "phone" else None,
        "instructions": instructions(db, profile, session.channel, session.location),
        "greeting": profile.greeting,
        "stt": profile.stt_provider,
        "tts": profile.tts_provider,
        "voice": profile.voice,
        "tools": tool_list(db, profile),
        "mcp_servers": [{"name": s.name, "url": s.url, "headers": s.headers} for s in servers],
    }
