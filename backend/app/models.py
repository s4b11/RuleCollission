import secrets
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def new_code() -> str:
    return secrets.token_hex(3).upper()


def now() -> datetime:
    return datetime.now(timezone.utc)


def pk():
    return mapped_column(String(12), primary_key=True, default=new_id)


def fk(target: str, nullable: bool = False):
    return mapped_column(ForeignKey(target), nullable=nullable, index=True)


def created():
    return mapped_column(DateTime(timezone=True), default=now)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = pk()
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    subject_label: Mapped[str] = mapped_column(String(60), default="Person")


class StaffUser(Base):
    __tablename__ = "staff_users"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    email: Mapped[str] = mapped_column(String(200), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))
    office: Mapped[str] = mapped_column(String(60))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class RulePackVersion(Base):
    __tablename__ = "rulepack_versions"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    pack_id: Mapped[str] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(String(200), default="seed")
    created_at: Mapped[datetime] = created()


class RuleDraft(Base):
    __tablename__ = "rule_drafts"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    pack_id: Mapped[str] = mapped_column(String(80))
    source: Mapped[str] = mapped_column(String(20))
    source_ref: Mapped[str] = mapped_column(String(200), default="")
    proposal: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewed_by: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = created()


class AgentProfile(Base):
    __tablename__ = "agent_profiles"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    pack_id: Mapped[str] = mapped_column(String(80))
    default_goal: Mapped[str] = mapped_column(String(80), default="")
    prompt: Mapped[str] = mapped_column(Text, default="")
    greeting: Mapped[str] = mapped_column(Text, default="")
    stt_provider: Mapped[str] = mapped_column(String(20), default="deepgram")
    tts_provider: Mapped[str] = mapped_column(String(20), default="deepgram")
    voice: Mapped[str] = mapped_column(String(100), default="")
    identifier_label: Mapped[str] = mapped_column(String(80), default="Reference number")
    identifier_pattern: Mapped[str] = mapped_column(String(120), default="")
    second_factor_label: Mapped[str] = mapped_column(String(80), default="")
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    phone_number: Mapped[str] = mapped_column(String(30), default="")
    enabled_tools: Mapped[list] = mapped_column(JSON, default=list)


class ToolDefinition(Base):
    __tablename__ = "tool_definitions"
    __table_args__ = (UniqueConstraint("org_id", "name"),)
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text)
    parameters: Mapped[dict] = mapped_column(JSON)
    url: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10), default="POST")
    headers: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class McpServer(Base):
    __tablename__ = "mcp_servers"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    name: Mapped[str] = mapped_column(String(80))
    url: Mapped[str] = mapped_column(String(500))
    headers: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    profile_id: Mapped[str] = fk("agent_profiles.id")
    label: Mapped[str] = mapped_column(String(120))


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    title: Mapped[str] = mapped_column(String(200))
    filename: Mapped[str] = mapped_column(String(200))
    storage_key: Mapped[str] = mapped_column(String(300))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = created()


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    document_id: Mapped[str] = fk("knowledge_documents.id")
    page: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(JSON)


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("org_id", "identifier"),)
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    identifier: Mapped[str] = mapped_column(String(60))
    second_factor: Mapped[str] = mapped_column(String(60), default="")
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(60), default="")
    status: Mapped[str] = mapped_column(String(40), default="active")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    documents: Mapped[list["SubjectDocument"]] = relationship(cascade="all, delete-orphan")


class SubjectDocument(Base):
    __tablename__ = "subject_documents"
    id: Mapped[str] = pk()
    subject_id: Mapped[str] = fk("subjects.id")
    document: Mapped[str] = mapped_column(String(80))
    issued_by: Mapped[str] = mapped_column(String(200), default="")
    issued_on: Mapped[date] = mapped_column(Date, default=date.today)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    subject_id: Mapped[str] = fk("subjects.id")
    code: Mapped[str] = mapped_column(String(8), unique=True, default=new_code)
    pack_id: Mapped[str] = mapped_column(String(80))
    goal: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="new")
    reported: Mapped[list] = mapped_column(JSON, default=list)
    alias_claims: Mapped[list] = mapped_column(JSON, default=list)
    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    subject: Mapped[Subject] = relationship()
    decisions: Mapped[list["Decision"]] = relationship(cascade="all, delete-orphan")
    notes: Mapped[list["CaseNote"]] = relationship(cascade="all, delete-orphan", order_by="CaseNote.created_at")
    reviews: Mapped[list["ReviewRequest"]] = relationship(cascade="all, delete-orphan")


class Decision(Base):
    __tablename__ = "decisions"
    id: Mapped[str] = pk()
    case_id: Mapped[str] = fk("cases.id")
    kind: Mapped[str] = mapped_column(String(40))
    target: Mapped[str] = mapped_column(String(200))
    staff_id: Mapped[str] = fk("staff_users.id")
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = created()
    staff: Mapped[StaffUser] = relationship()


class ReviewRequest(Base):
    __tablename__ = "review_requests"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    case_id: Mapped[str] = fk("cases.id")
    key: Mapped[str] = mapped_column(String(300), unique=True)
    kind: Mapped[str] = mapped_column(String(40))
    about: Mapped[str] = mapped_column(String(200))
    target_office: Mapped[str] = mapped_column(String(60), default="")
    question: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")
    answer: Mapped[str] = mapped_column(Text, default="")
    answered_by: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = created()


class CaseNote(Base):
    __tablename__ = "case_notes"
    id: Mapped[str] = pk()
    case_id: Mapped[str] = fk("cases.id")
    author: Mapped[str] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created()


class AgentSession(Base):
    __tablename__ = "agent_sessions"
    id: Mapped[str] = pk()
    org_id: Mapped[str] = fk("organizations.id")
    profile_id: Mapped[str] = fk("agent_profiles.id")
    token: Mapped[str] = mapped_column(String(64), default=lambda: secrets.token_urlsafe(24))
    channel: Mapped[str] = mapped_column(String(10), default="web")
    room: Mapped[str] = mapped_column(String(100), default="")
    location: Mapped[str] = mapped_column(String(120), default="")
    caller: Mapped[str] = mapped_column(String(40), default="")
    subject_id: Mapped[str | None] = fk("subjects.id", nullable=True)
    case_id: Mapped[str | None] = fk("cases.id", nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = created()
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transcript: Mapped[list["TranscriptLine"]] = relationship(cascade="all, delete-orphan", order_by="TranscriptLine.at")


class TranscriptLine(Base):
    __tablename__ = "transcript_lines"
    id: Mapped[str] = pk()
    session_id: Mapped[str] = fk("agent_sessions.id")
    role: Mapped[str] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)
    at: Mapped[datetime] = created()


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"
    id: Mapped[str] = pk()
    session_id: Mapped[str] = fk("agent_sessions.id")
    tool: Mapped[str] = mapped_column(String(64))
    arguments: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    at: Mapped[datetime] = created()
