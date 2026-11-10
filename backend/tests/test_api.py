from conftest import AGENT

from app.db import SessionLocal
from app.models import AgentProfile, AgentSession
from app.services import llm
from app.tools import http_tool


def new_session(channel: str = "web") -> str:
    with SessionLocal() as db:
        profile = db.query(AgentProfile).filter_by(slug="sunrise-discharge").one()
        session = AgentSession(org_id=profile.org_id, profile_id=profile.id, channel=channel)
        db.add(session)
        db.commit()
        return session.id


def call(client, session_id: str, tool: str, **arguments) -> dict:
    response = client.post(f"/internal/agent/sessions/{session_id}/tools/{tool}",
                           json={"arguments": arguments}, headers=AGENT)
    assert response.status_code == 200
    return response.json()


def case_for(client, headers, name: str) -> dict:
    return next(c for c in client.get("/ops/cases", headers=headers).json() if c["subject"] == name)


def review(client, headers, case_id: str, kind: str) -> dict:
    reviews = client.get("/ops/reviews?mine=false", headers=headers).json()
    return next(r for r in reviews if r["case_id"] == case_id and r["kind"] == kind)


def test_login_rejects_wrong_password(client):
    assert client.post("/auth/login", json={"email": "billing@sunrise.example", "password": "nope"}).status_code == 401
    assert client.get("/ops/cases").status_code == 401


def test_h1_deadlock_resolved_by_staff_decisions(client, login):
    billing, tpa, ward = login("billing@sunrise.example"), login("tpa@sunrise.example"), login("ward@sunrise.example")
    case = case_for(client, billing, "Arjun Menon")
    assert case["status"] == "needs_decision"
    detail = client.get(f"/ops/cases/{case['id']}", headers=billing).json()
    assert detail["summary"]["blockers"][0]["documents"] == ["Final hospital bill", "Final cashless approval"]

    approval = review(client, billing, case["id"], "alternative_approval")
    refused = client.post(f"/ops/reviews/{approval['id']}/answer", json={"agree": True}, headers=ward)
    assert refused.status_code == 403
    assert case_for(client, billing, "Arjun Menon")["status"] == "needs_decision"

    assert client.post(f"/ops/reviews/{approval['id']}/answer", json={"agree": True}, headers=billing).status_code == 200
    assert case_for(client, billing, "Arjun Menon")["status"] == "needs_decision"

    acceptance = review(client, tpa, case["id"], "alternative_acceptance")
    assert client.post(f"/ops/reviews/{acceptance['id']}/answer", json={"agree": True}, headers=tpa).status_code == 200
    detail = client.get(f"/ops/cases/{case['id']}", headers=billing).json()
    assert detail["summary"]["status"] == "route_confirmed"
    assert detail["summary"]["steps"][0]["document"] == "Interim (provisional) bill"


def test_issuing_the_goal_document_completes_the_case(client, login):
    ward = login("ward@sunrise.example")
    case = case_for(client, ward, "Lakshmi Iyer")
    subject_id = client.get(f"/ops/cases/{case['id']}", headers=ward).json()["subject_id"]
    client.post(f"/ops/subjects/{subject_id}/documents", json={"document": "discharge_authorization"}, headers=ward)
    assert case_for(client, ward, "Lakshmi Iyer")["status"] == "completed"


def test_agent_endpoints_need_the_agent_key(client):
    session_id = new_session()
    assert client.get(f"/internal/agent/sessions/{session_id}/config").status_code == 401


def test_session_config_is_built_from_the_database(client, login):
    admin = login("admin@sunrise.example")
    config = client.get(f"/internal/agent/sessions/{new_session()}/config", headers=AGENT).json()
    assert config["max_seconds"] is None
    assert "add_case_note" in [t["name"] for t in config["tools"]]

    profile = client.get("/studio/profiles", headers=admin).json()[0]
    profile["enabled_tools"] = [t for t in profile["enabled_tools"] if t != "add_case_note"]
    profile["prompt"] = "Always mention the help desk."
    assert client.put(f"/studio/profiles/{profile['id']}", json=profile, headers=admin).status_code == 200

    session_id = new_session("phone")
    config = client.get(f"/internal/agent/sessions/{session_id}/config", headers=AGENT).json()
    assert config["max_seconds"] == 180
    assert "Always mention the help desk." in config["instructions"]
    assert "add_case_note" not in [t["name"] for t in config["tools"]]
    assert "not enabled" in call(client, session_id, "add_case_note", text="x")["error"]


def test_agent_must_identify_before_case_tools(client):
    session_id = new_session()
    assert "not identified" in call(client, session_id, "get_case_status")["error"]
    assert call(client, session_id, "identify_subject", identifier="SGH-2026-0421")["identified"] is False
    wrong = call(client, session_id, "identify_subject", identifier="SGH-2026-0421", second_factor="1999")
    assert wrong == {"identified": False, "attempts_left": 2}
    found = call(client, session_id, "identify_subject", identifier="sgh 2026 0421", second_factor="1950")
    assert found["identified"] and found["name"] == "Joseph Mathew"
    assert found["case"]["status"] == "needs_decision"


def test_agent_proposals_stay_unverified_and_cannot_decide(client, login):
    doctor = login("doctor@sunrise.example")
    session_id = new_session()
    call(client, session_id, "identify_subject", identifier="SGH-2026-0421", second_factor="1950")
    result = call(client, session_id, "propose_requirement", office="doctor", issues="discharge_summary",
                  needs_first=["lab_summary", "billing_clearance"], quote="Summary only after billing clears you")
    assert result["status"] == "needs_information"
    assert any(q["kind"] == "verify_requirement" for q in result["questions"])
    assert "error" in call(client, session_id, "approve_alternative", target="alt_interim_bill")

    case = case_for(client, doctor, "Joseph Mathew")
    question = review(client, doctor, case["id"], "verify_requirement")
    client.post(f"/ops/reviews/{question['id']}/answer", json={"agree": False, "note": "Not our rule"}, headers=doctor)
    assert client.get(f"/ops/cases/{case['id']}", headers=doctor).json()["reported"] == []


def test_knowledge_search_returns_cited_passages(client):
    session_id = new_session()
    passages = call(client, session_id, "search_knowledge", query="who can approve an interim bill")["passages"]
    assert passages and passages[0]["document"] == "Discharge and cashless claims handbook"


def test_organisations_cannot_see_each_other(client, login):
    hospital, company = login("billing@sunrise.example"), login("admin@northwind.example")
    case = case_for(client, hospital, "Arjun Menon")
    assert client.get(f"/ops/cases/{case['id']}", headers=company).status_code == 404
    assert [c["subject"] for c in client.get("/ops/cases", headers=company).json()] == ["Rohit Sen"]


def test_only_admins_open_the_studio(client, login):
    assert client.get("/studio/profiles", headers=login("billing@sunrise.example")).status_code == 403


def test_rule_draft_needs_staff_approval(client, login, monkeypatch):
    admin = login("admin@sunrise.example")
    proposal = {
        "documents": [{"id": "pharmacy_clearance", "name": "Pharmacy clearance"}],
        "requirements": [{"id": "hd_pharmacy", "office": "billing", "produces": "pharmacy_clearance",
                          "prerequisites": "final_bill", "quote": "Pharmacy dues are cleared after the final bill."}],
    }
    monkeypatch.setattr(llm, "chat_json", lambda system, messages: {"reply": "Drafted.", "proposal": proposal})
    answer = client.post("/studio/rulepacks/hospital_discharge/drafts/chat",
                         json={"messages": [{"role": "user", "content": "Pharmacy clears after the final bill"}]},
                         headers=admin).json()
    draft = answer["draft"]
    assert draft["status"] == "pending" and draft["problems"] == []

    before = client.get("/studio/rulepacks/hospital_discharge", headers=admin).json()
    assert "hd_pharmacy" not in [r["id"] for r in before["data"]["requirements"]]

    client.post(f"/studio/drafts/{draft['id']}/approve", json={}, headers=admin)
    after = client.get("/studio/rulepacks/hospital_discharge", headers=admin).json()
    assert "hd_pharmacy" in [r["id"] for r in after["data"]["requirements"]]
    assert after["versions"][0]["version"] == before["versions"][0]["version"] + 1


def test_invalid_rule_draft_is_refused(client, login, monkeypatch):
    admin = login("admin@sunrise.example")
    bad = {"requirements": [{"id": "x", "office": "nowhere", "produces": "final_bill"}]}
    monkeypatch.setattr(llm, "chat_json", lambda system, messages: {"reply": "", "proposal": bad})
    draft = client.post("/studio/rulepacks/hospital_discharge/drafts/chat", json={"messages": []},
                        headers=admin).json()["draft"]
    assert "unknown office" in " ".join(draft["problems"])
    assert client.post(f"/studio/drafts/{draft['id']}/approve", json={}, headers=admin).status_code == 422


def test_external_tools_cannot_reach_private_addresses(client, login):
    admin = login("admin@sunrise.example")
    body = {"name": "probe", "description": "x", "parameters": {"type": "object", "properties": {}}}
    for url in ("http://example.com/hook", "https://127.0.0.1/hook", "https://localhost/hook"):
        assert client.post("/studio/tools", json={**body, "url": url}, headers=admin).status_code == 422
    try:
        http_tool.check_url("https://10.0.0.5/x")
        assert False
    except ValueError:
        pass


def test_public_case_lookup_needs_code_and_identifier(client, login):
    case = case_for(client, login("billing@sunrise.example"), "Fatima Sheikh")
    wrong = client.post("/public/cases/lookup", json={"code": case["code"], "identifier": "SGH-2026-0000"})
    assert wrong.status_code == 404
    right = client.post("/public/cases/lookup", json={"code": case["code"], "identifier": "SGH-2026-0407"})
    assert right.json()["summary"]["subject"] == "Fatima Sheikh"
    assert any("expired" in note for note in right.json()["summary"]["notes"])


def test_qr_code_points_to_the_web_app(client, login):
    admin = login("admin@sunrise.example")
    profile = client.get("/studio/profiles", headers=admin).json()[0]
    location = client.get(f"/studio/profiles/{profile['id']}/locations", headers=admin).json()[0]
    assert location["link"].endswith(f"/a/sunrise-discharge?loc={location['id']}")
    assert client.get(f"/public/qr/{location['id']}.svg").text.startswith("<?xml")
