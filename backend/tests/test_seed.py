import tempfile

import pytest
from sqlalchemy.orm import sessionmaker

from app.db import Base, make_engine
from app.models import (
    AgentSession, Case, Decision, KnowledgeDocument, Location, Organization, ReviewRequest, StaffUser, Subject,
)
from app.seed import demo

TABLES = [Organization, StaffUser, Subject, Case, Decision, ReviewRequest, AgentSession, Location, KnowledgeDocument]


def fresh_db():
    engine = make_engine(f"sqlite:///{tempfile.mkdtemp()}/seed.db")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def counts(db):
    return {table.__tablename__: db.query(table).count() for table in TABLES}


@pytest.fixture(scope="module")
def seeded():
    db = fresh_db()
    demo.seed_demo(db)
    return db


def test_seeding_twice_adds_nothing(seeded):
    before = counts(seeded)
    demo.seed_demo(seeded)
    assert counts(seeded) == before


def test_seed_adds_new_data_to_an_old_database(monkeypatch):
    db = fresh_db()
    monkeypatch.setattr(demo, "PATIENTS", demo.PATIENTS[:12])
    monkeypatch.setattr(demo, "HOSPITAL_STAFF", demo.HOSPITAL_STAFF[:6])
    monkeypatch.setattr(demo, "EMPLOYEES", demo.EMPLOYEES[:3])
    monkeypatch.setattr(demo, "CORPORATE_STAFF", demo.CORPORATE_STAFF[:2])
    demo.seed_demo(db)
    old_case = db.query(Case).filter_by(code="SGH412").one().id
    old_staff = db.query(StaffUser).count()
    monkeypatch.undo()

    demo.seed_demo(db)
    assert db.query(Subject).count() == len(demo.PATIENTS) + len(demo.EMPLOYEES)
    assert db.query(StaffUser).filter_by(email="legal@northwind.example").one()
    assert db.query(Case).filter_by(code="SGH412").one().id == old_case
    assert db.query(StaffUser).count() == old_staff + 6 + 6
    assert db.query(Organization).count() == 2


@pytest.mark.parametrize("code, status", [
    ("SGH412", "needs_decision"),
    ("SGH415", "route_confirmed"),
    ("SGH398", "completed"),
    ("SGH425", "needs_decision"),
    ("SGH426", "unresolved"),
    ("SGH427", "needs_information"),
    ("SGH429", "needs_information"),
    ("NW1042", "needs_decision"),
    ("NW1051", "route_confirmed"),
    ("NW1088", "needs_information"),
    ("NW1110", "needs_decision"),
    ("NW1112", "route_confirmed"),
    ("NW1019", "completed"),
])
def test_seeded_cases_reach_their_intended_outcome(seeded, code, status):
    assert seeded.query(Case).filter_by(code=code).one().status == status


def test_every_seeded_user_can_sign_in(client):
    for email, *_ in demo.HOSPITAL_STAFF + demo.CORPORATE_STAFF:
        assert client.post("/auth/login", json={"email": email, "password": "demo1234"}).status_code == 200, email
