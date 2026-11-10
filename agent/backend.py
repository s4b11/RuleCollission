import os

import httpx


class Backend:
    """The agent's only link to the application. Configuration and tools live there."""

    def __init__(self) -> None:
        self.http = httpx.AsyncClient(
            base_url=os.environ["BACKEND_URL"] + "/internal/agent",
            headers={"X-Agent-Key": os.environ["AGENT_API_KEY"]},
            timeout=20,
        )

    async def session_config(self, session_id: str) -> dict:
        response = await self.http.get(f"/sessions/{session_id}/config")
        response.raise_for_status()
        return response.json()

    async def start_phone_session(self, dialed_number: str, caller: str, room: str) -> dict:
        body = {"dialed_number": dialed_number, "caller": caller, "room": room}
        response = await self.http.post("/phone-sessions", json=body)
        response.raise_for_status()
        return response.json()

    async def call_tool(self, session_id: str, name: str, arguments: dict) -> dict:
        response = await self.http.post(f"/sessions/{session_id}/tools/{name}", json={"arguments": arguments})
        return response.json()

    async def add_transcript(self, session_id: str, role: str, text: str) -> None:
        await self.http.post(f"/sessions/{session_id}/transcript", json={"role": role, "text": text})

    async def end_session(self, session_id: str) -> None:
        await self.http.post(f"/sessions/{session_id}/end")
