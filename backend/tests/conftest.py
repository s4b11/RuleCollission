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
