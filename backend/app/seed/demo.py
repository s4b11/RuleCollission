"""Fictional demo data. No real patient, employee or institution appears here."""

from datetime import date, timedelta
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from .. import config
from ..models import AgentProfile, Location, Organization, StaffUser, Subject, SubjectDocument
from ..rag.ingest import add_document
from ..security import hash_password
from ..services import cases
from ..services.rulepacks import save_version
from ..tools.builtin import TOOLS

FILES = Path(__file__).parent / "files"
TODAY = date.today()

HOSPITAL_PROMPT = (
    "Help patients and families understand what is holding up a discharge. Speak calmly and plainly. "
    "Explain one step at a time and say which desk to go to next."
)

HOSPITAL_STAFF = [
    ("admin@sunrise.example", "Meera Nair", "approver", "insurance_desk", True),
    ("billing@sunrise.example", "Priya Raman", "approver", "billing", False),
    ("tpa@sunrise.example", "Vikram Shah", "approver", "tpa", False),
    ("doctor@sunrise.example", "Dr. Kavya Pillai", "approver", "doctor", False),
    ("lab@sunrise.example", "Imran Qureshi", "desk_staff", "lab", False),
    ("ward@sunrise.example", "Anil Thomas", "desk_staff", "ward", False),
]

BASIC = ["policy_card", "admission_note"]
READY = BASIC + ["preauth_approval", "lab_summary", "discharge_summary"]
DONE = READY + ["final_bill", "final_insurer_approval", "billing_clearance", "discharge_authorization"]

# name, admission number, birth year, ward, bed, doctor, reason, insurer, days admitted, estimate, documents
PATIENTS = [
    ("Arjun Menon", "SGH-2026-0412", "1958", "Ward 3 · General", "3-07", "Dr. Kavya Pillai", "Pneumonia", "Asha Health", 6, 84500, READY),
    ("Lakshmi Iyer", "SGH-2026-0415", "1971", "Ward 5 · Surgical", "5-02", "Dr. Rohan Das", "Gallbladder surgery", "Asha Health", 4, 132000, READY),
    ("Rahul Verma", "SGH-2026-0398", "1989", "Ward 3 · General", "3-11", "Dr. Kavya Pillai", "Dengue fever", "Asha Health", 7, 46200, DONE),
    ("Fatima Sheikh", "SGH-2026-0407", "1964", "Ward 5 · Surgical", "5-09", "Dr. Rohan Das", "Knee replacement", "Asha Health", 9, 218000, BASIC + ["preauth_approval", "lab_summary"]),
    ("Joseph Mathew", "SGH-2026-0421", "1950", "Ward 2 · Cardiac", "2-04", "Dr. Sneha Kulkarni", "Chest pain observation", "Asha Health", 1, 38000, BASIC),
    ("Ananya Rao", "SGH-2026-0418", "1995", "Ward 4 · Maternity", "4-03", "Dr. Farah Ali", "Caesarean delivery", "Asha Health", 3, 96000, BASIC + ["preauth_approval", "lab_summary"]),
    ("Suresh Patil", "SGH-2026-0409", "1947", "Ward 2 · Cardiac", "2-01", "Dr. Sneha Kulkarni", "Angioplasty", "Asha Health", 5, 265000, READY),
    ("Deepa Krishnan", "SGH-2026-0420", "1983", "Ward 3 · General", "3-02", "Dr. Kavya Pillai", "Typhoid", "Asha Health", 2, 29500, BASIC + ["preauth_approval"]),
    ("Mohammed Rafi", "SGH-2026-0416", "1976", "Ward 5 · Surgical", "5-06", "Dr. Rohan Das", "Hernia repair", "Asha Health", 3, 74000, BASIC + ["preauth_approval", "lab_summary"]),
    ("Gita Banerjee", "SGH-2026-0402", "1939", "Ward 2 · Cardiac", "2-08", "Dr. Sneha Kulkarni", "Heart failure care", "Asha Health", 11, 187000, READY),
    ("Nikhil Joshi", "SGH-2026-0422", "2001", "Ward 3 · General", "3-05", "Dr. Kavya Pillai", "Appendicitis", "Asha Health", 1, 58000, BASIC),
    ("Shalini Gupta", "SGH-2026-0413", "1968", "Ward 4 · Maternity", "4-08", "Dr. Farah Ali", "Fibroid surgery", "Asha Health", 4, 112000, BASIC + ["preauth_approval", "lab_summary"]),
]

CORPORATE_STAFF = [
    ("admin@northwind.example", "Tara Bose", "approver", "hr", True),
    ("it@northwind.example", "Kiran Reddy", "approver", "it", False),
]

EMPLOYEES = [
    ("Rohit Sen", "NW-1042", "Engineering · leaving", ["resignation_letter", "resignation_acceptance", "access_card_return"]),
    ("Pooja Nambiar", "NW-1077", "Design · leaving", ["resignation_letter"]),
    ("Aditya Kapoor", "NW-1103", "Sales · joining", ["offer_acceptance"]),
]


def load_pack(name: str) -> dict:
    return yaml.safe_load((config.RULEPACK_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def add_staff(db: Session, org: Organization, rows: list) -> dict[str, StaffUser]:
    users = {}
    for email, name, role, office, is_admin in rows:
        user = StaffUser(org_id=org.id, email=email, name=name, role=role, office=office, is_admin=is_admin,
                         password_hash=hash_password(config.DEMO_PASSWORD))
        db.add(user)
        users[office] = user
    db.flush()
    return users


def add_profile(db: Session, org: Organization, slug: str, name: str, pack_id: str, goal: str, prompt: str,
                greeting: str, identifier: str, second_factor: str) -> AgentProfile:
    profile = AgentProfile(
        org_id=org.id, slug=slug, name=name, pack_id=pack_id, default_goal=goal, prompt=prompt, greeting=greeting,
        identifier_label=identifier, second_factor_label=second_factor, enabled_tools=list(TOOLS),
    )
    db.add(profile)
    db.flush()
    return profile


def seed_hospital(db: Session) -> None:
    org = Organization(slug="sunrise", name="Sunrise General Hospital (fictional)", subject_label="Patient")
    db.add(org)
    db.flush()
    staff = add_staff(db, org, HOSPITAL_STAFF)
    save_version(db, org.id, load_pack("hospital_discharge"), "seed")
    profile = add_profile(
        db, org, "sunrise-discharge", "Sunrise Discharge Assistant", "hospital_discharge", "discharge_authorization",
        HOSPITAL_PROMPT, "Hello, this is the Sunrise discharge assistant. May I have the patient's admission number?",
        "admission number", "year of birth",
    )
    for label in ("Main Reception", "Ward 3 Nursing Station", "Billing Counter"):
        db.add(Location(org_id=org.id, profile_id=profile.id, label=label))

    subjects = {}
    for name, number, year, ward, bed, doctor, reason, insurer, days, estimate, documents in PATIENTS:
        subject = Subject(
            org_id=org.id, identifier=number, second_factor=year, name=name,
            status="discharged" if documents is DONE else "admitted",
            details={"ward": ward, "bed": bed, "doctor": doctor, "reason": reason, "insurer": insurer,
                     "admitted_on": str(TODAY - timedelta(days=days)), "bill_estimate": estimate},
        )
        for document in documents:
            subject.documents.append(SubjectDocument(document=document, issued_by="seed",
                                                     issued_on=TODAY - timedelta(days=max(days - 1, 0))))
        db.add(subject)
        subjects[name] = subject
    db.flush()

    expired = next(d for d in subjects["Fatima Sheikh"].documents if d.document == "preauth_approval")
    expired.expires_on = TODAY - timedelta(days=1)

    for name in ("Arjun Menon", "Lakshmi Iyer", "Rahul Verma", "Fatima Sheikh", "Joseph Mathew"):
        cases.open_case(db, subjects[name], "hospital_discharge", "discharge_authorization")
    resolved = cases.open_case(db, subjects["Lakshmi Iyer"], "hospital_discharge", "discharge_authorization")
    cases.record_decision(db, resolved, staff["billing"], "approve_alternative", "alt_interim_bill",
                          note="Interim bill approved for this admission")
    cases.record_decision(db, resolved, staff["tpa"], "accept_alternative", "alt_interim_bill",
                          note="TPA will accept the interim bill for final approval")

    handbook = (FILES / "sunrise_discharge_handbook.md").read_bytes()
    add_document(db, org.id, "Discharge and cashless claims handbook", "sunrise_discharge_handbook.md", handbook)


def seed_corporate(db: Session) -> None:
    org = Organization(slug="northwind", name="Northwind Labs (fictional)", subject_label="Employee")
    db.add(org)
    db.flush()
    add_staff(db, org, CORPORATE_STAFF)
    save_version(db, org.id, load_pack("corporate_lifecycle"), "seed")
    add_profile(
        db, org, "northwind-people", "Northwind People Desk", "corporate_lifecycle", "",
        "Help employees understand joining and leaving formalities.",
        "Hello, this is the Northwind people desk. What is your employee number?", "employee number", "",
    )
    for name, number, team, documents in EMPLOYEES:
        subject = Subject(org_id=org.id, identifier=number, name=name, details={"team": team})
        for document in documents:
            subject.documents.append(SubjectDocument(document=document, issued_by="seed"))
        db.add(subject)
    db.flush()
    leaving = db.query(Subject).filter_by(org_id=org.id, identifier="NW-1042").one()
    cases.open_case(db, leaving, "corporate_lifecycle", "relieving_letter")


def seed_if_empty(db: Session) -> None:
    if db.query(Organization).count():
        return
    seed_hospital(db)
    seed_corporate(db)
    db.commit()
