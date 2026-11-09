from datetime import date

from conftest import decide, make_case, staff

from app.engine import analyze
from app.engine.models import (
    AliasClaim,
    Condition,
    DecisionKind,
    HeldDocument,
    OutcomeStatus,
    Requirement,
    Role,
    RouteStatus,
    Source,
    SourceKind,
)

GOAL = "discharge_authorization"


def kinds(analysis):
    return {(c.kind, c.about, c.target_office) for c in analysis.clarifications}


def note_kinds(analysis):
    return {n.kind for n in analysis.notes}


# H1: billing <-> TPA deadlock, unlocked by the interim-bill alternative.
def test_h1_cycle_detected_with_candidate_alternative(hospital):
    a = analyze(hospital, make_case("h1", GOAL, ["policy_card"]))
    assert a.status == OutcomeStatus.needs_decision
    assert [g.documents for g in a.blocking_groups] == [["final_bill", "final_insurer_approval"]]
    assert a.blocking_groups[0].requirement_ids == ["hd_final_approval", "hd_final_bill"]
    [cand] = a.candidate_alternatives
    assert cand.alternative_id == "alt_interim_bill" and not cand.approved
    assert cand.pending_acceptance_from == ["tpa"]
    assert ("alternative_approval", "alt_interim_bill", "billing") in kinds(a)
    assert ("alternative_acceptance", "alt_interim_bill", "tpa") in kinds(a)


def test_h1_route_confirmed_after_approval_and_acceptance(hospital):
    case = make_case("h1", GOAL, ["policy_card"], decisions=[
        decide("h1", DecisionKind.approve_alternative, "alt_interim_bill", staff("billing")),
        decide("h1", DecisionKind.accept_alternative, "alt_interim_bill", staff("tpa")),
    ])
    a = analyze(hospital, case)
    assert a.status == OutcomeStatus.route_available
    assert a.route.status == RouteStatus.confirmed
    assert a.route.alternatives_used == ["alt_interim_bill"]
    order = [s.document for s in a.route.steps]
    assert order.index("interim_bill") < order.index("final_insurer_approval") < order.index("final_bill")
    assert order[-1] == GOAL


def test_h1_approval_without_acceptance_is_not_enough(hospital):
    case = make_case("h1", GOAL, ["policy_card"], decisions=[
        decide("h1", DecisionKind.approve_alternative, "alt_interim_bill", staff("billing")),
    ])
    a = analyze(hospital, case)
    assert a.status == OutcomeStatus.needs_decision
    [cand] = a.candidate_alternatives
    assert cand.approved and cand.pending_acceptance_from == ["tpa"]


# H2: reported ward/billing dependency creates a cycle no alternative can break.
def _h2_requirement():
    return Requirement(
        id="h2_reported_summary",
        office="doctor",
        produces="discharge_summary",
        prerequisites={"all_of": ["lab_summary", "billing_clearance"]},
        source=Source(kind=SourceKind.applicant_report, quote="The summary is released only after billing clears you."),
    )


def test_h2_unverified_cycle_needs_information(hospital):
    a = analyze(hospital, make_case("h2", GOAL, ["policy_card"], reported_requirements=[_h2_requirement()]))
    assert a.status == OutcomeStatus.needs_information
    assert a.candidate_alternatives == []
    [group] = a.blocking_groups
    assert set(group.documents) == {"billing_clearance", "discharge_summary", "final_bill", "final_insurer_approval"}
    assert ("verify_requirement", "h2_reported_summary", "doctor") in kinds(a)


def test_h2_verified_cycle_is_unresolved_with_decision_request(hospital):
    case = make_case("h2", GOAL, ["policy_card"], reported_requirements=[_h2_requirement()], decisions=[
        decide("h2", DecisionKind.verify_requirement, "h2_reported_summary", staff("doctor", Role.desk_staff)),
    ])
    a = analyze(hospital, case)
    assert a.status == OutcomeStatus.unresolved
    assert any(c.kind == "decision_request" for c in a.clarifications)


# H3: "investigation report" vs "lab summary".
def _h3_case(decisions=()):
    req = Requirement(
        id="h3_tpa_query",
        office="tpa",
        produces="preauth_approval",
        prerequisites={"all_of": ["admission_note", "policy_card", "investigation_report"]},
        source=Source(kind=SourceKind.staff_statement, quote="Send the investigation report."),
    )
    verify = decide("h3", DecisionKind.verify_requirement, "h3_tpa_query", staff("tpa", Role.desk_staff))
    return make_case("h3", "preauth_approval", ["policy_card"], reported_requirements=[req],
                     alias_claims=[AliasClaim(term="investigation_report", document="lab_summary", office="tpa")],
                     decisions=[verify, *decisions])


def test_h3_terminology_mismatch_asks_for_equivalence(hospital):
    a = analyze(hospital, _h3_case())
    assert a.status == OutcomeStatus.needs_information
    assert a.blocking_groups == []
    assert ("unconfirmed_equivalence", "investigation_report", "tpa") in kinds(a)
    assert a.missing_documents == []


def test_h3_confirmed_equivalence_removes_conflict(hospital):
    eq = decide("h3", DecisionKind.confirm_equivalence, "investigation_report=lab_summary", staff("tpa"))
    a = analyze(hospital, _h3_case([eq]))
    assert a.status == OutcomeStatus.route_available
    assert a.route.status == RouteStatus.confirmed
    assert [s.document for s in a.route.steps] == ["admission_note", "lab_summary", "preauth_approval"]
    assert "equivalence_applied" in note_kinds(a)


def test_h3_equivalence_from_unrelated_office_rejected(hospital):
    eq = decide("h3", DecisionKind.confirm_equivalence, "investigation_report=lab_summary", staff("billing"))
    a = analyze(hospital, _h3_case([eq]))
    assert a.status == OutcomeStatus.needs_information
    assert "rejected_decision" in note_kinds(a)


# H4: outdated room-rent rule.
def test_h4_outdated_instruction_is_flagged_and_current_rule_used(hospital):
    outdated = Requirement(
        id="h4_old_instruction",
        office="tpa",
        produces="preauth_approval",
        prerequisites={"all_of": ["admission_note", "policy_card", "room_rent_declaration"]},
        cites_rule="hd_preauth_v1",
        source=Source(kind=SourceKind.applicant_report),
    )
    a = analyze(hospital, make_case("h4", "preauth_approval", ["policy_card"], reported_requirements=[outdated]))
    assert "version_mismatch" in note_kinds(a)
    assert a.status == OutcomeStatus.route_available
    assert a.route.steps[-1].requirement_ids == ["hd_preauth_v2"]


def test_h4_old_version_applies_on_older_date(hospital):
    a = analyze(hospital, make_case("h4", "preauth_approval", ["policy_card"], as_of=date(2026, 3, 1)))
    assert a.status == OutcomeStatus.needs_information
    assert a.missing_documents == ["room_rent_declaration"]


# H5: expired pre-authorisation and expired approval.
def test_h5_expired_document_must_be_reobtained(hospital):
    case = make_case("h5", "preauth_approval", ["policy_card", "admission_note"])
    case.held.append(HeldDocument(document="preauth_approval", expires_on=date(2026, 5, 20)))
    a = analyze(hospital, case)
    assert "expired_document" in note_kinds(a)
    assert a.route.steps[-1].document == "preauth_approval"


def test_h5_expired_decision_is_ignored(hospital):
    case = make_case("h5", GOAL, ["policy_card"], decisions=[
        decide("h5", DecisionKind.approve_alternative, "alt_interim_bill", staff("billing"), valid_until=date(2026, 5, 25)),
        decide("h5", DecisionKind.accept_alternative, "alt_interim_bill", staff("tpa")),
    ])
    a = analyze(hospital, case)
    assert "expired_decision" in note_kinds(a)
    assert a.status == OutcomeStatus.needs_decision


# H6: authority checks.
def test_h6_nurse_cannot_approve_alternative(hospital):
    case = make_case("h6", GOAL, ["policy_card"], decisions=[
        decide("h6", DecisionKind.approve_alternative, "alt_interim_bill", staff("ward", Role.desk_staff)),
        decide("h6", DecisionKind.accept_alternative, "alt_interim_bill", staff("tpa")),
    ])
    a = analyze(hospital, case)
    assert a.status == OutcomeStatus.needs_decision
    assert not a.candidate_alternatives[0].approved
    assert "rejected_decision" in note_kinds(a)


def test_h6_desk_staff_cannot_accept_alternative(hospital):
    case = make_case("h6", GOAL, ["policy_card"], decisions=[
        decide("h6", DecisionKind.approve_alternative, "alt_interim_bill", staff("billing")),
        decide("h6", DecisionKind.accept_alternative, "alt_interim_bill", staff("tpa", Role.desk_staff)),
    ])
    assert analyze(hospital, case).status == OutcomeStatus.needs_decision


def test_decision_from_another_case_is_not_reused(hospital):
    case = make_case("h7", GOAL, ["policy_card"], decisions=[
        decide("h1", DecisionKind.approve_alternative, "alt_interim_bill", staff("billing")),
        decide("h1", DecisionKind.accept_alternative, "alt_interim_bill", staff("tpa")),
    ])
    a = analyze(hospital, case)
    assert a.status == OutcomeStatus.needs_decision
    assert "rejected_decision" in note_kinds(a)


def test_applicant_cannot_record_decisions(hospital):
    case = make_case("h8", GOAL, ["policy_card"], decisions=[
        decide("h8", DecisionKind.approve_alternative, "alt_interim_bill", staff("billing", Role.applicant)),
    ])
    assert "rejected_decision" in note_kinds(analyze(hospital, case))


# Generic case types.
def test_goal_already_held(hospital):
    a = analyze(hospital, make_case("g1", "preauth_approval", ["preauth_approval"]))
    assert a.status == OutcomeStatus.route_available
    assert a.route.steps == [] and "already_held" in note_kinds(a)


def test_held_prerequisite_breaks_cycle(hospital):
    a = analyze(hospital, make_case("g2", GOAL, ["policy_card", "final_insurer_approval"]))
    assert a.status == OutcomeStatus.route_available
    assert a.route.status == RouteStatus.confirmed


def test_unknown_document_is_missing_information(hospital):
    req = Requirement(id="g3_noc", office="ward", produces="discharge_authorization",
                      prerequisites={"all_of": ["billing_clearance", "ward_noc"]},
                      source=Source(kind=SourceKind.applicant_report))
    a = analyze(hospital, make_case("g3", GOAL, ["policy_card"], reported_requirements=[req]))
    assert a.status in (OutcomeStatus.needs_information, OutcomeStatus.needs_decision)
    assert "ward_noc" in a.missing_documents


def test_incompatible_conditions_are_flagged(hospital):
    reqs = [
        Requirement(id="g4_doctor", office="doctor", produces="discharge_summary", prerequisites="lab_summary",
                    conditions=[Condition(document="lab_summary", attribute="signed_by", equals="pathologist")],
                    verified=True),
        Requirement(id="g4_lab", office="lab", produces="lab_summary", prerequisites="admission_note",
                    conditions=[Condition(document="lab_summary", attribute="signed_by", equals="lab_technician")],
                    verified=True),
    ]
    a = analyze(hospital, make_case("g4", "discharge_summary", [], reported_requirements=reqs))
    assert a.status == OutcomeStatus.needs_decision
    assert a.condition_conflicts == [["g4_doctor", "g4_lab"]]
    assert a.route.status == RouteStatus.suggested


def test_applicability_unknown_asks_and_known_category_filters(hospital):
    req = Requirement(id="g5_senior", office="tpa", produces="preauth_approval",
                      prerequisites={"all_of": ["admission_note", "policy_card", "room_rent_declaration"]},
                      applies_to={"applicant_category": ["senior_citizen"]}, verified=True)
    unknown = analyze(hospital, make_case("g5", "preauth_approval", ["policy_card"], reported_requirements=[req]))
    assert any(c.kind == "applicability" for c in unknown.clarifications)

    general = analyze(hospital, make_case("g5", "preauth_approval", ["policy_card"], reported_requirements=[req],
                                          applicant_category="general"))
    assert general.status == OutcomeStatus.route_available
    assert general.route.steps[-1].requirement_ids == ["hd_preauth_v2"]


def test_correction_from_both_to_either_changes_outcome(hospital):
    def req(prereqs):
        return Requirement(id="g6_reported", office="tpa", produces="preauth_approval", prerequisites=prereqs,
                           source=Source(kind=SourceKind.applicant_report))

    both = analyze(hospital, make_case("g6", "preauth_approval", ["policy_card"],
                                       reported_requirements=[req({"all_of": ["admission_note", "policy_card", "room_rent_declaration"]})]))
    assert both.status == OutcomeStatus.needs_information

    either = analyze(hospital, make_case("g6", "preauth_approval", ["policy_card"],
                                         reported_requirements=[req({"all_of": ["admission_note", {"any_of": ["policy_card", "room_rent_declaration"]}]})]))
    assert either.status == OutcomeStatus.route_available
    assert either.route.status == RouteStatus.suggested
    assert either.route.unverified_requirements == ["g6_reported"]
