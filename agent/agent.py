"""The single LiveKit agent. It knows nothing about any organisation: prompt, voice,
tools and MCP servers are fetched from the backend when each session starts."""

import asyncio
import json
import os

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, RunContext, cli, function_tool, mcp
from livekit.agents.llm import FallbackAdapter
from livekit.plugins import cartesia, deepgram, groq, openai, silero

from backend import Backend
from base_prompt import BASE_PROMPT

load_dotenv()

AGENT_NAME = os.environ.get("LIVEKIT_AGENT_NAME", "rulecollision")
WARNING_SECONDS = 20

server = AgentServer()


def make_tool(backend: Backend, session_id: str, spec: dict):
    async def handler(raw_arguments: dict[str, object], context: RunContext):
        return await backend.call_tool(session_id, spec["name"], raw_arguments)

    return function_tool(handler, raw_schema=spec)


def make_llm():
    models = []
    if os.environ.get("GROQ_API_KEY"):
        models.append(groq.LLM(model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")))
    if os.environ.get("OPENAI_API_KEY"):
        models.append(openai.LLM(model=os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")))
    return models[0] if len(models) == 1 else FallbackAdapter(models)


def make_stt(provider: str):
    return cartesia.STT() if provider == "cartesia" else deepgram.STT(model="nova-3")


def make_tts(provider: str, voice: str):
    if provider == "cartesia":
        return cartesia.TTS(voice=voice) if voice else cartesia.TTS()
    return deepgram.TTS(model=voice or "aura-2-andromeda-en")


async def load_config(ctx: JobContext, backend: Backend, participant: rtc.RemoteParticipant) -> dict:
    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        attributes = participant.attributes
        return await backend.start_phone_session(
            attributes.get("sip.trunkPhoneNumber", ""), attributes.get("sip.phoneNumber", ""), ctx.room.name
        )
    metadata = json.loads(ctx.job.metadata or "{}")
    return await backend.session_config(metadata["session_id"])


async def end_call_at_limit(ctx: JobContext, session: AgentSession, seconds: int) -> None:
    await asyncio.sleep(seconds - WARNING_SECONDS)
    await session.say("We have about twenty seconds left on this call. You can continue on the web app with your case code.")
    await asyncio.sleep(WARNING_SECONDS)
    await session.say("Thank you for calling. Goodbye.", allow_interruptions=False)
    await ctx.delete_room()


def listen_for_keypad(ctx: JobContext, session: AgentSession) -> None:
    digits: list[str] = []

    def on_key(event: rtc.SipDTMF) -> None:
        if event.digit != "#":
            digits.append(event.digit)
            return
        entered = "".join(digits)
        digits.clear()
        session.generate_reply(user_input=f"I typed this on the keypad: {entered}")

    ctx.room.on("sip_dtmf_received", on_key)


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    participant = await ctx.wait_for_participant()
    backend = Backend()
    config = await load_config(ctx, backend, participant)
    session_id = config["session_id"]

    session = AgentSession(
        stt=make_stt(config["stt"]),
        llm=make_llm(),
        tts=make_tts(config["tts"], config["voice"]),
        vad=silero.VAD.load(),
        mcp_servers=[mcp.MCPServerHTTP(url=s["url"], headers=s["headers"]) for s in config["mcp_servers"]],
    )
    agent = Agent(
        instructions=f"{BASE_PROMPT}\n\n{config['instructions']}",
        tools=[make_tool(backend, session_id, spec) for spec in config["tools"]],
    )

    def save_line(event) -> None:
        text = getattr(event.item, "text_content", None)
        if text:
            asyncio.create_task(backend.add_transcript(session_id, event.item.role, text))

    session.on("conversation_item_added", save_line)
    ctx.add_shutdown_callback(lambda: backend.end_session(session_id))

    await session.start(agent=agent, room=ctx.room)
    if config["channel"] == "phone":
        listen_for_keypad(ctx, session)
    if config["max_seconds"]:
        asyncio.create_task(end_call_at_limit(ctx, session, config["max_seconds"]))
    if config["greeting"]:
        await session.say(config["greeting"])


if __name__ == "__main__":
    cli.run_app(server)
