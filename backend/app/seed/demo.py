"""Fictional demo data. No real patient, employee or institution appears here.

seed_demo runs at every start and only adds what is missing: organisations by slug, staff by email,
people by identifier, locations by label and knowledge documents by file name. A person's case history
is written only when the person is new, so restarts never duplicate or overwrite anything.
"""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from .. import config
from ..models import (
    AgentProfile, AgentSession, Case, CaseNote, KnowledgeDocument, Location, Organization, StaffUser, Subject,
    SubjectDocument, TranscriptLine,
)
from ..rag.ingest import add_document
from ..security import hash_password
from ..services import cases
from ..services.rulepacks import save_version
from ..tools.builtin import TOOLS

FILES = Path(__file__).parent / "files"
TODAY = date.today()

# ---------------------------------------------------------------- hospital

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
    ("rohan.das@sunrise.example", "Dr. Rohan Das", "approver", "doctor", False),
    ("sneha.kulkarni@sunrise.example", "Dr. Sneha Kulkarni", "approver", "doctor", False),
    ("farah.ali@sunrise.example", "Dr. Farah Ali", "approver", "doctor", False),
    ("billing.desk@sunrise.example", "Joel Fernandes", "desk_staff", "billing", False),
    ("insurance@sunrise.example", "Bindu Varghese", "desk_staff", "insurance_desk", False),
    ("ward.night@sunrise.example", "Reshma Pillai", "desk_staff", "ward", False),
]

BASIC = ["policy_card", "admission_note"]
PREAUTH = BASIC + ["preauth_approval"]
LAB = PREAUTH + ["lab_summary"]
READY = LAB + ["discharge_summary"]
DONE = READY + ["final_bill", "final_insurer_approval", "billing_clearance", "discharge_authorization"]
GOAL = "discharge_authorization"

APPROVE_INTERIM = ("billing@sunrise.example", "approve_alternative", "alt_interim_bill",
                   "Interim bill approved for this admission")
ACCEPT_INTERIM = ("tpa@sunrise.example", "accept_alternative", "alt_interim_bill",
                  "TPA will accept the interim bill for final approval")


def patient(name, number, year, ward, bed, doctor, reason, days, estimate, documents, **history):
    return {
        "name": name, "identifier": number, "second_factor": year, "documents": documents, "days": days,
        "status": "discharged" if documents is DONE else "admitted",
        "details": {"ward": ward, "bed": bed, "doctor": doctor, "reason": reason, "insurer": "Asha Health",
                    "admitted_on": str(TODAY - timedelta(days=days)), "bill_estimate": estimate},
        **history,
    }


PATIENTS = [
    patient("Arjun Menon", "SGH-2026-0412", "1958", "Ward 3 · General", "3-07", "Dr. Kavya Pillai", "Pneumonia",
            6, 84500, READY, case=GOAL, code="SGH412"),
    patient("Lakshmi Iyer", "SGH-2026-0415", "1971", "Ward 5 · Surgical", "5-02", "Dr. Rohan Das",
            "Gallbladder surgery", 4, 132000, READY, case=GOAL, code="SGH415",
            decisions=[APPROVE_INTERIM, ACCEPT_INTERIM]),
    patient("Rahul Verma", "SGH-2026-0398", "1989", "Ward 3 · General", "3-11", "Dr. Kavya Pillai", "Dengue fever",
            7, 46200, DONE, case=GOAL, code="SGH398"),
    patient("Fatima Sheikh", "SGH-2026-0407", "1964", "Ward 5 · Surgical", "5-09", "Dr. Rohan Das",
            "Knee replacement", 9, 218000, LAB, case=GOAL, code="SGH407", expired=["preauth_approval"]),
    patient("Joseph Mathew", "SGH-2026-0421", "1950", "Ward 2 · Cardiac", "2-04", "Dr. Sneha Kulkarni",
            "Chest pain observation", 1, 38000, BASIC, case=GOAL, code="SGH421"),
    patient("Ananya Rao", "SGH-2026-0418", "1995", "Ward 4 · Maternity", "4-03", "Dr. Farah Ali",
            "Caesarean delivery", 3, 96000, LAB),
    patient("Suresh Patil", "SGH-2026-0409", "1947", "Ward 2 · Cardiac", "2-01", "Dr. Sneha Kulkarni", "Angioplasty",
            5, 265000, READY),
    patient("Deepa Krishnan", "SGH-2026-0420", "1983", "Ward 3 · General", "3-02", "Dr. Kavya Pillai", "Typhoid",
            2, 29500, PREAUTH),
    patient("Mohammed Rafi", "SGH-2026-0416", "1976", "Ward 5 · Surgical", "5-06", "Dr. Rohan Das", "Hernia repair",
            3, 74000, LAB),
    patient("Gita Banerjee", "SGH-2026-0402", "1939", "Ward 2 · Cardiac", "2-08", "Dr. Sneha Kulkarni",
            "Heart failure care", 11, 187000, READY),
    patient("Nikhil Joshi", "SGH-2026-0422", "2001", "Ward 3 · General", "3-05", "Dr. Kavya Pillai", "Appendicitis",
            1, 58000, BASIC),
    patient("Shalini Gupta", "SGH-2026-0413", "1968", "Ward 4 · Maternity", "4-08", "Dr. Farah Ali",
            "Fibroid surgery", 4, 112000, LAB),
    # Added in the second round of demo data.
    patient("Kavitha Reddy", "SGH-2026-0424", "1962", "Ward 3 · General", "3-09", "Dr. Kavya Pillai",
            "Urinary tract infection", 3, 41500, READY, case=GOAL, code="SGH424",
            decisions=[APPROVE_INTERIM, ACCEPT_INTERIM],
            notes=[("Priya Raman", "Family informed that the interim bill route is approved.")],
            talk=("web", "Main Reception", [
                ("user", "My mother is ready to go home but billing says they are waiting for the insurance."),
                ("assistant", "I can check that. May I have the admission number?"),
                ("user", "SGH-2026-0424, she was born in 1962."),
                ("assistant", "Thank you. Billing has approved an interim bill and the TPA has accepted it. "
                              "The next step is the interim bill from the Billing Department."),
            ])),
    patient("Sanjay Kulkarni", "SGH-2026-0425", "1955", "Ward 2 · Cardiac", "2-06", "Dr. Sneha Kulkarni",
            "Pacemaker implant", 6, 312000, READY, case=GOAL, code="SGH425", decisions=[APPROVE_INTERIM],
            notes=[("Priya Raman", "Interim bill approved. Waiting for the TPA to accept it.")]),
    patient("Meenakshi Pillai", "SGH-2026-0426", "1948", "Ward 2 · Cardiac", "2-03", "Dr. Sneha Kulkarni",
            "Arrhythmia monitoring", 4, 67000, READY, case=GOAL, code="SGH426",
            decisions=[("billing@sunrise.example", "refuse_alternative", "alt_interim_bill",
                        "Pre-authorisation amount is under review; no interim bill for now")],
            notes=[("Meera Nair", "Escalated to the hospital administrator for a decision.")]),
    patient("Harish Chandra", "SGH-2026-0427", "1972", "Ward 5 · Surgical", "5-04", "Dr. Rohan Das",
            "Spine surgery", 8, 245000, READY, case=GOAL, code="SGH427",
            reported=[("tpa", "final_insurer_approval", ["final_bill", "discharge_summary", "discharge_authorization"],
                       "The TPA counter said they need the discharge pass before the final approval.")],
            talk=("phone", "", [
                ("assistant", "Hello, this is the Sunrise discharge assistant. May I have the admission number?"),
                ("user", "It is SGH-2026-0427. Year of birth 1972."),
                ("user", "The TPA counter told me they need the discharge pass before they give final approval."),
                ("assistant", "I have noted that as something the TPA told you. The TPA office will be asked to "
                              "confirm it, because the hospital rules do not list it."),
            ])),
    patient("Rekha Bhat", "SGH-2026-0428", "1980", "Ward 4 · Maternity", "4-05", "Dr. Farah Ali", "Normal delivery",
            2, 48000, PREAUTH, case=GOAL, code="SGH428"),
    patient("Vivek Anand", "SGH-2026-0429", "1991", "Ward 3 · General", "3-01", "Dr. Kavya Pillai",
            "Food poisoning", 2, 22000, READY, case=GOAL, code="SGH429",
            reported=[("tpa", "final_insurer_approval", ["final_bill", "discharge_summary", "investigation_report"],
                       "The TPA asked us to send the investigation report with the bill.")],
            aliases=[("investigation_report", "lab_summary", "tpa")],
            talk=("web", "Ward 3 Nursing Station", [
                ("user", "The TPA wants an investigation report. What is that?"),
                ("assistant", "It may be the laboratory summary, which you already have. Only the TPA can confirm "
                              "that, so I have asked them."),
            ])),
    patient("Zoya Khan", "SGH-2026-0430", "1999", "Ward 4 · Maternity", "4-01", "Dr. Farah Ali",
            "Ovarian cyst surgery", 3, 89000, LAB, case=GOAL, code="SGH430"),
    patient("Prakash Nair", "SGH-2026-0431", "1945", "Ward 2 · Cardiac", "2-10", "Dr. Sneha Kulkarni",
            "Bypass surgery", 12, 398000, READY, case=GOAL, code="SGH431", expired=["preauth_approval"],
            notes=[("Bindu Varghese", "Stay extended by four days; fresh pre-authorisation requested.")]),
    patient("Divya Menon", "SGH-2026-0432", "1987", "Ward 5 · Surgical", "5-01", "Dr. Rohan Das",
            "Fracture fixation", 5, 121000, DONE, case=GOAL, code="SGH432"),
    patient("Ramesh Iyer", "SGH-2026-0433", "1966", "Ward 3 · General", "3-12", "Dr. Kavya Pillai",
            "Diabetes control", 4, 36000, READY, case=GOAL, code="SGH433",
            talk=("web", "Billing Counter", [
                ("user", "Billing wants the insurance approval and the insurance wants the bill. What do I do?"),
                ("assistant", "You are right, those two wait on each other. The hospital has an approved way out: "
                              "an interim bill. I have asked Billing to decide on it for you."),
            ])),
    patient("Nisha Agarwal", "SGH-2026-0434", "1993", "Ward 4 · Maternity", "4-06", "Dr. Farah Ali",
            "Caesarean delivery", 4, 102000, READY, case=GOAL, code="SGH434"),
    patient("Thomas George", "SGH-2026-0435", "1959", "Ward 5 · Surgical", "5-08", "Dr. Rohan Das",
            "Prostate surgery", 1, 143000, BASIC),
    patient("Sunita Desai", "SGH-2026-0436", "1974", "Ward 3 · General", "3-04", "Dr. Kavya Pillai",
            "Kidney stones", 1, 52000, BASIC, case=GOAL, code="SGH436"),
    patient("Abdul Karim", "SGH-2026-0437", "1952", "Ward 2 · Cardiac", "2-07", "Dr. Sneha Kulkarni",
            "Stroke rehabilitation", 10, 176000, READY, case=GOAL, code="SGH437",
            decisions=[APPROVE_INTERIM, ACCEPT_INTERIM]),
]

HOSPITAL_LOCATIONS = ["Main Reception", "Ward 3 Nursing Station", "Billing Counter", "Emergency Desk",
                      "Ward 5 Nursing Station", "Insurance Desk"]
HOSPITAL_FILES = [
    ("Discharge and cashless claims handbook", "sunrise_discharge_handbook.md"),
    ("Visitor and billing questions", "sunrise_visitor_and_billing_faq.md"),
]

# ---------------------------------------------------------------- company

CORPORATE_STAFF = [
    ("admin@northwind.example", "Tara Bose", "approver", "hr", True),
    ("it@northwind.example", "Kiran Reddy", "approver", "it", False),
    ("hr.desk@northwind.example", "Sneha Paul", "desk_staff", "hr", False),
    ("finance@northwind.example", "Sandeep Ghosh", "approver", "finance", False),
    ("facilities@northwind.example", "Lina D'Souza", "approver", "admin", False),
    ("manager@northwind.example", "Rajiv Malik", "approver", "manager", False),
    ("legal@northwind.example", "Nandini Rao", "approver", "legal", False),
    ("security@northwind.example", "Kabir Singh", "approver", "security", False),
]

LEAVE = "relieving_letter"
JOIN = "joining_letter"
EMPLOYEE_ID = "employee_id"
APPROVE_EXIT = ("admin@northwind.example", "approve_alternative", "alt_provisional_exit",
                "Provisional exit ticket approved")
ACCEPT_EXIT = ("it@northwind.example", "accept_alternative", "alt_provisional_exit",
               "IT accepts the provisional exit ticket for asset clearance")
APPROVE_PAPER = ("legal@northwind.example", "approve_alternative", "alt_paper_nda", "Wet-ink NDA approved")
ACCEPT_PAPER = ("admin@northwind.example", "accept_alternative", "alt_paper_nda",
                "HR accepts the paper NDA to issue the employee ID")
LEFT = ["resignation_letter", "resignation_acceptance", "access_card_return"]
JOINED = ["offer_acceptance", "bgv_report", "joining_letter", "signed_nda", "employee_id", "laptop_issued"]


def employee(name, number, team, documents, **history):
    return {"name": name, "identifier": number, "second_factor": "", "documents": documents, "days": 0,
            "status": "active", "details": {"team": team}, **history}


EMPLOYEES = [
    employee("Rohit Sen", "NW-1042", "Engineering · leaving", LEFT, case=LEAVE, code="NW1042"),
    employee("Pooja Nambiar", "NW-1077", "Design · leaving", ["resignation_letter"]),
    employee("Aditya Kapoor", "NW-1103", "Sales · joining", ["offer_acceptance"]),
    # Added in the second round of demo data.
    employee("Neha Kulkarni", "NW-1051", "Engineering · leaving", LEFT, case=LEAVE, code="NW1051",
             decisions=[APPROVE_EXIT, ACCEPT_EXIT],
             notes=[("Tara Bose", "Last working day confirmed; provisional exit route agreed with IT.")]),
    employee("Sameer Joshi", "NW-1066", "Finance · leaving", ["resignation_letter", "resignation_acceptance"],
             case=LEAVE, code="NW1066", decisions=[APPROVE_EXIT]),
    employee("Ritu Malhotra", "NW-1019", "Marketing · left",
             LEFT + ["hr_exit_record", "it_asset_clearance", "no_dues_certificate", "full_and_final_settlement",
                     "relieving_letter"], case=LEAVE, code="NW1019"),
    employee("Arvind Rao", "NW-1088", "Support · leaving", LEFT, case=LEAVE, code="NW1088",
             reported=[("finance", "full_and_final_settlement", ["hr_exit_record", "clearance_form", "relieving_letter"],
                        "Payroll told me they settle dues only after the relieving letter is issued.")],
             talk=("web", "HR Help Desk", [
                 ("user", "Payroll says they settle my dues only after HR gives the relieving letter."),
                 ("assistant", "HR issues the relieving letter only after the settlement, so that would be a loop. "
                               "I have noted it and asked Finance to confirm."),
             ])),
    employee("Leela Menon", "NW-1071", "People team · leaving", ["resignation_letter"], case=LEAVE, code="NW1071"),
    employee("Meghna Iyer", "NW-1059", "Operations · leaving", ["resignation_letter", "resignation_acceptance"],
             case=LEAVE, code="NW1059"),
    employee("Isha Verma", "NW-1110", "Design · joining", ["offer_acceptance"], case=EMPLOYEE_ID, code="NW1110",
             talk=("web", "Reception", [
                 ("user", "HR wants the NDA before my ID, Legal wants my laptop first, and IT wants my ID."),
                 ("assistant", "Those three wait on each other. Legal can approve a paper NDA instead; "
                               "I have asked Legal to decide."),
             ])),
    employee("Karan Mehta", "NW-1112", "Engineering · joining", ["offer_acceptance"], case=EMPLOYEE_ID,
             code="NW1112", decisions=[APPROVE_PAPER, ACCEPT_PAPER]),
    employee("Ananya Das", "NW-1115", "Sales · joining", ["offer_acceptance"], case=JOIN, code="NW1115"),
    employee("Farhan Ali", "NW-1098", "Engineering · joined", JOINED, case=EMPLOYEE_ID, code="NW1098"),
    employee("Varun Shetty", "NW-1117", "Data · joining", ["offer_acceptance"]),
]

CORPORATE_LOCATIONS = ["Reception", "HR Help Desk", "IT Service Desk"]
CORPORATE_FILES = [("Joining and leaving guide", "northwind_joining_and_leaving_guide.md")]

# ---------------------------------------------------------------- helpers


def load_pack(name: str) -> dict:
    return yaml.safe_load((config.RULEPACK_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def ensure_staff(db: Session, org: Organization, rows: list) -> dict[str, StaffUser]:
    users = {u.email: u for u in db.query(StaffUser).filter_by(org_id=org.id)}
    for email, name, role, office, is_admin in rows:
        if email not in users:
            users[email] = StaffUser(org_id=org.id, email=email, name=name, role=role, office=office,
                                     is_admin=is_admin, password_hash=hash_password(config.DEMO_PASSWORD))
            db.add(users[email])
    db.flush()
    return users


def ensure_profile(db: Session, org: Organization, slug: str, **fields) -> AgentProfile:
    profile = db.query(AgentProfile).filter_by(org_id=org.id, slug=slug).first()
    if not profile:
        profile = AgentProfile(org_id=org.id, slug=slug, enabled_tools=list(TOOLS), **fields)
        db.add(profile)
        db.flush()
    return profile


def ensure_locations(db: Session, org: Organization, profile: AgentProfile, labels: list[str]) -> None:
    existing = {l.label for l in db.query(Location).filter_by(org_id=org.id)}
    for label in labels:
        if label not in existing:
            db.add(Location(org_id=org.id, profile_id=profile.id, label=label))


def ensure_files(db: Session, org: Organization, files: list[tuple[str, str]]) -> None:
    existing = {d.filename for d in db.query(KnowledgeDocument).filter_by(org_id=org.id)}
    for title, filename in files:
        if filename not in existing:
            add_document(db, org.id, title, filename, (FILES / filename).read_bytes())


def add_people(db: Session, org: Organization, pack_id: str, staff: dict[str, StaffUser], people: list) -> None:
    existing = {s.identifier for s in db.query(Subject).filter_by(org_id=org.id)}
    for spec in people:
        if spec["identifier"] in existing:
            continue
        subject = Subject(org_id=org.id, identifier=spec["identifier"], second_factor=spec["second_factor"],
                          name=spec["name"], status=spec["status"], details=spec["details"])
        issued = TODAY - timedelta(days=max(spec["days"] - 1, 0))
        for document in spec["documents"]:
            expires = TODAY - timedelta(days=1) if document in spec.get("expired", []) else None
            subject.documents.append(SubjectDocument(document=document, issued_by="seed", issued_on=issued,
                                                     expires_on=expires))
        db.add(subject)
        db.flush()
        if spec.get("case"):
            add_history(db, org, pack_id, staff, subject, spec)


def add_history(db: Session, org: Organization, pack_id: str, staff: dict[str, StaffUser], subject: Subject,
                spec: dict) -> None:
    case = cases.open_case(db, subject, pack_id, spec["case"])
    if spec.get("code") and not db.query(Case).filter_by(code=spec["code"]).first():
        case.code = spec["code"]
    if spec.get("reported") or spec.get("aliases"):
        case.reported = [
            {"id": f"rep_seed_{office}_{issues}", "office": office, "produces": issues,
             "prerequisites": {"all_of": needs}, "source": {"kind": "applicant_report", "quote": quote}}
            for office, issues, needs, quote in spec.get("reported", [])
        ]
        case.alias_claims = [{"term": t, "document": d, "office": o} for t, d, o in spec.get("aliases", [])]
        cases.analyze_case(db, case)
    for email, kind, target, note in spec.get("decisions", []):
        cases.record_decision(db, case, staff[email], kind, target, note=note)
    for author, text in spec.get("notes", []):
        case.notes.append(CaseNote(author=author, text=text))
    if spec.get("talk"):
        channel, location, lines = spec["talk"]
        start = datetime.now(timezone.utc) - timedelta(hours=3)
        profile = db.query(AgentProfile).filter_by(org_id=org.id).first()
        session = AgentSession(org_id=org.id, profile_id=profile.id, channel=channel, location=location,
                               caller="+1 555 0100" if channel == "phone" else "", subject_id=subject.id,
                               case_id=case.id, started_at=start, ended_at=start + timedelta(minutes=2))
        for index, (role, text) in enumerate(lines):
            session.transcript.append(TranscriptLine(role=role, text=text, at=start + timedelta(seconds=20 * index)))
        db.add(session)
    db.flush()


def ensure_org(db: Session, slug: str, name: str, subject_label: str, pack: str) -> Organization:
    org = db.query(Organization).filter_by(slug=slug).first()
    if not org:
        org = Organization(slug=slug, name=name, subject_label=subject_label)
        db.add(org)
        db.flush()
        save_version(db, org.id, load_pack(pack), "seed")
    return org


# ---------------------------------------------------------------- seeding


def seed_hospital(db: Session) -> None:
    org = ensure_org(db, "sunrise", "Sunrise General Hospital (fictional)", "Patient", "hospital_discharge")
    staff = ensure_staff(db, org, HOSPITAL_STAFF)
    profile = ensure_profile(
        db, org, "sunrise-discharge", name="Sunrise Discharge Assistant", pack_id="hospital_discharge",
        default_goal=GOAL, prompt=HOSPITAL_PROMPT,
        greeting="Hello, this is the Sunrise discharge assistant. May I have the patient's admission number?",
        identifier_label="admission number", second_factor_label="year of birth",
    )
    ensure_locations(db, org, profile, HOSPITAL_LOCATIONS)
    add_people(db, org, "hospital_discharge", staff, PATIENTS)
    ensure_files(db, org, HOSPITAL_FILES)


def seed_corporate(db: Session) -> None:
    org = ensure_org(db, "northwind", "Northwind Labs (fictional)", "Employee", "corporate_lifecycle")
    staff = ensure_staff(db, org, CORPORATE_STAFF)
    profile = ensure_profile(
        db, org, "northwind-people", name="Northwind People Desk", pack_id="corporate_lifecycle", default_goal="",
        prompt="Help employees understand joining and leaving formalities.",
        greeting="Hello, this is the Northwind people desk. What is your employee number?",
        identifier_label="employee number", second_factor_label="",
    )
    ensure_locations(db, org, profile, CORPORATE_LOCATIONS)
    add_people(db, org, "corporate_lifecycle", staff, EMPLOYEES)
    ensure_files(db, org, CORPORATE_FILES)


def seed_demo(db: Session) -> None:
    seed_hospital(db)
    seed_corporate(db)
    db.commit()
