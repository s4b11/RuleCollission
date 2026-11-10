import io
import json

import segno
from livekit import api

from .. import config
from ..models import AgentProfile, AgentSession, Location


def voice_ready() -> bool:
    return bool(config.LIVEKIT_URL and config.LIVEKIT_API_KEY and config.LIVEKIT_API_SECRET)


def room_token(session: AgentSession) -> str:
    dispatch = api.RoomAgentDispatch(
        agent_name=config.LIVEKIT_AGENT_NAME, metadata=json.dumps({"session_id": session.id})
    )
    token = (
        api.AccessToken(config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
        .with_identity(f"visitor-{session.id}")
        .with_grants(api.VideoGrants(room_join=True, room=session.room))
        .with_room_config(api.RoomConfiguration(agents=[dispatch]))
    )
    return token.to_jwt()


def web_link(profile: AgentProfile, location: Location | None = None) -> str:
    link = f"{config.WEB_APP_URL}/a/{profile.slug}"
    return f"{link}?loc={location.id}" if location else link


def qr_svg(link: str) -> str:
    buffer = io.BytesIO()
    segno.make(link, error="m").save(buffer, kind="svg", scale=6, border=2)
    return buffer.getvalue().decode()
