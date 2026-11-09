from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Literal, Union

from pydantic import BaseModel, Field

# A prerequisite expression is a document id, {"all_of": [...]}, or {"any_of": [...]}.
Expr = Union[str, dict[str, list[Any]]]


class Role(str, Enum):
    applicant = "applicant"
    desk_staff = "desk_staff"
    approver = "approver"


class SourceKind(str, Enum):
    approved_rule = "approved_rule"
    staff_statement = "staff_statement"
    applicant_report = "applicant_report"
    document = "document"


class Office(BaseModel):
    id: str
    name: str


class Document(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)


class Condition(BaseModel):
    document: str
    attribute: str
    equals: str


class Source(BaseModel):
    kind: SourceKind = SourceKind.approved_rule
    evidence_id: str | None = None
    quote: str | None = None


class Requirement(BaseModel):
    id: str
    office: str
    produces: str
    prerequisites: Expr | None = None
    conditions: list[Condition] = Field(default_factory=list)
    applies_to: dict[str, list[str]] = Field(default_factory=dict)
    effective_from: date | None = None
    effective_until: date | None = None
    source: Source = Field(default_factory=Source)
    verified: bool | None = None
    cites_rule: str | None = None

    @property
    def is_verified(self) -> bool:
        if self.verified is not None:
            return self.verified
        return self.source.kind == SourceKind.approved_rule


class Alternative(BaseModel):
    """An institution-approved substitute document, usable only after case-scoped approval and acceptance."""

    id: str
    office: str
    produces: str
    prerequisites: Expr | None = None
    substitutes: str
    in_offices: list[str]
    approval_by: str
    description: str = ""


class StaffIdentity(BaseModel):
    staff_id: str
    role: Role
    office: str


class DecisionKind(str, Enum):
    verify_requirement = "verify_requirement"
    approve_alternative = "approve_alternative"
    refuse_alternative = "refuse_alternative"
    accept_alternative = "accept_alternative"
    confirm_equivalence = "confirm_equivalence"
    reject_equivalence = "reject_equivalence"


class Decision(BaseModel):
    id: str
    case_id: str
    kind: DecisionKind
    target: str
    by: StaffIdentity
    valid_until: date | None = None
    note: str | None = None


class HeldDocument(BaseModel):
    document: str
    expires_on: date | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class AliasClaim(BaseModel):
    term: str
    document: str
    office: str


class Case(BaseModel):
    id: str
    goal: str
    as_of: date
    applicant_category: str | None = None
    held: list[HeldDocument] = Field(default_factory=list)
    reported_requirements: list[Requirement] = Field(default_factory=list)
    alias_claims: list[AliasClaim] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)


class RulePack(BaseModel):
    pack_id: str
    name: str
    description: str = ""
    offices: list[Office]
    documents: list[Document]
    requirements: list[Requirement]
    alternatives: list[Alternative] = Field(default_factory=list)


# ---------- Analysis output ----------


class OutcomeStatus(str, Enum):
    route_available = "route_available"
    needs_information = "needs_information"
    needs_decision = "needs_decision"
    unresolved = "unresolved"


class RouteStatus(str, Enum):
    suggested = "suggested"
    confirmed = "confirmed"


class RouteStep(BaseModel):
    order: int
    document: str
    offices: list[str]
    requirement_ids: list[str]
    via_alternative: str | None = None


class Route(BaseModel):
    status: RouteStatus
    steps: list[RouteStep]
    unverified_requirements: list[str] = Field(default_factory=list)
    alternatives_used: list[str] = Field(default_factory=list)


class BlockingGroup(BaseModel):
    documents: list[str]
    requirement_ids: list[str]
    sources: dict[str, Source]


class Clarification(BaseModel):
    kind: Literal[
        "missing_document",
        "unconfirmed_equivalence",
        "applicability",
        "condition_conflict",
        "verify_requirement",
        "alternative_approval",
        "alternative_acceptance",
        "decision_request",
    ]
    about: str
    target_office: str | None
    question: str


class Note(BaseModel):
    kind: Literal[
        "expired_document",
        "version_mismatch",
        "rejected_decision",
        "expired_decision",
        "refused_alternative",
        "equivalence_applied",
        "already_held",
    ]
    detail: str


class CandidateAlternative(BaseModel):
    alternative_id: str
    approved: bool
    refused: bool
    pending_acceptance_from: list[str]


class Analysis(BaseModel):
    case_id: str
    goal: str
    status: OutcomeStatus
    route: Route | None = None
    blocking_groups: list[BlockingGroup] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    condition_conflicts: list[list[str]] = Field(default_factory=list)
    candidate_alternatives: list[CandidateAlternative] = Field(default_factory=list)
    clarifications: list[Clarification] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
