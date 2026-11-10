import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["FILES_DIR"] = tempfile.mkdtemp()
os.environ["EMBEDDER"] = "hash"
os.environ["LIVEKIT_URL"] = ""

from datetime import date

import pytest

from app.engine import load_rulepack
from app.engine.models import Case, Decision, DecisionKind, HeldDocument, Role, StaffIdentity

AS_OF = date(2026, 6, 1)


@pytest.fixture(scope="session")
def hospital():
    return load_rulepack("hospital_discharge")


@pytest.fixture(scope="session")
def corporate():
    return load_rulepack("corporate_lifecycle")


def staff(office: str, role: Role = Role.approver, sid: str | None = None) -> StaffIdentity:
    return StaffIdentity(staff_id=sid or f"{office}_{role.value}", role=role, office=office)


def decide(case_id: str, kind: DecisionKind, target: str, by: StaffIdentity, **kw) -> Decision:
    return Decision(id=f"d_{kind.value}_{target}_{by.staff_id}", case_id=case_id, kind=kind, target=target, by=by, **kw)


def make_case(case_id: str, goal: str, held: list[str], **kw) -> Case:
    kw.setdefault("as_of", AS_OF)
    return Case(id=case_id, goal=goal, held=[HeldDocument(document=d) for d in held], **kw)


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def login(client):
    def sign_in(email: str) -> dict:
        response = client.post("/auth/login", json={"email": email, "password": "demo1234"})
        return {"Authorization": f"Bearer {response.json()['token']}"}
    return sign_in


AGENT = {"X-Agent-Key": "dev-agent-key"}
