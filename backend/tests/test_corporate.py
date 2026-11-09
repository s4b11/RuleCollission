import pytest
from conftest import decide, make_case, staff

from app.engine import analyze
from app.engine.loader import RulePackError, validate
from app.engine.models import DecisionKind, OutcomeStatus, Requirement, Role, RouteStatus, Source, SourceKind


# C1 + C2: offboarding HR <-> IT deadlock; "clearance form" is an approved alias of "no-dues certificate".
def test_c1_offboarding_cycle_with_candidate(corporate):
    a = analyze(corporate, make_case("c1", "relieving_letter", ["resignation_letter", "access_card_return"]))
    assert a.status == OutcomeStatus.needs_decision
    assert [g.documents for g in a.blocking_groups] == [["hr_exit_record", "it_asset_clearance"]]
    [cand] = a.candidate_alternatives
    assert cand.alternative_id == "alt_provisional_exit" and cand.pending_acceptance_from == ["it"]


def test_c1_route_after_provisional_exit_ticket(corporate):
    case = make_case("c1", "relieving_letter", ["resignation_letter", "access_card_return"], decisions=[
        decide("c1", DecisionKind.approve_alternative, "alt_provisional_exit", staff("hr")),
        decide("c1", DecisionKind.accept_alternative, "alt_provisional_exit", staff("it")),
    ])
    a = analyze(corporate, case)
    assert a.route.status == RouteStatus.confirmed
    docs = [s.document for s in a.route.steps]
    assert docs.index("provisional_exit_ticket") < docs.index("it_asset_clearance") < docs.index("hr_exit_record")
    assert "no_dues_certificate" in docs
    assert any(n.kind == "equivalence_applied" and "clearance_form" in n.detail for n in a.notes)


def test_c1_already_holding_exit_record_needs_no_alternative(corporate):
    a = analyze(corporate, make_case("c1b", "relieving_letter",
                                     ["resignation_letter", "access_card_return", "hr_exit_record"]))
    assert a.status == OutcomeStatus.route_available
    assert a.route.alternatives_used == []


# C3: three-way onboarding deadlock.
def test_c3_three_node_cycle_and_paper_nda(corporate):
    a = analyze(corporate, make_case("c3", "laptop_issued", ["offer_acceptance"]))
    assert [g.documents for g in a.blocking_groups] == [["employee_id", "laptop_issued", "signed_nda"]]
    assert a.candidate_alternatives[0].alternative_id == "alt_paper_nda"

    case = make_case("c3", "laptop_issued", ["offer_acceptance"], decisions=[
        decide("c3", DecisionKind.approve_alternative, "alt_paper_nda", staff("legal")),
        decide("c3", DecisionKind.accept_alternative, "alt_paper_nda", staff("hr")),
    ])
    a = analyze(corporate, case)
    assert [s.document for s in a.route.steps] == ["paper_nda", "employee_id", "laptop_issued"]


def test_c3_refused_alternative_leaves_case_unresolved(corporate):
    case = make_case("c3", "laptop_issued", ["offer_acceptance"], decisions=[
        decide("c3", DecisionKind.refuse_alternative, "alt_paper_nda", staff("legal")),
    ])
    a = analyze(corporate, case)
    assert a.status == OutcomeStatus.unresolved
    assert any(n.kind == "refused_alternative" for n in a.notes)


# C4: genuinely unresolved.
def test_c4_verified_cycle_without_alternative_is_unresolved(corporate):
    req = Requirement(id="c4_bgv", office="security", produces="bgv_report", prerequisites="joining_letter",
                      source=Source(kind=SourceKind.staff_statement, quote="We verify only after the joining letter."))
    case = make_case("c4", "joining_letter", ["offer_acceptance"], reported_requirements=[req], decisions=[
        decide("c4", DecisionKind.verify_requirement, "c4_bgv", staff("security", Role.desk_staff)),
    ])
    a = analyze(corporate, case)
    assert a.status == OutcomeStatus.unresolved
    [request] = [c for c in a.clarifications if c.kind == "decision_request"]
    assert "bgv_report" in request.question and "joining_letter" in request.question


def test_staff_from_other_office_cannot_verify(corporate):
    req = Requirement(id="c4_bgv", office="security", produces="bgv_report", prerequisites="joining_letter",
                      source=Source(kind=SourceKind.staff_statement))
    case = make_case("c4", "joining_letter", ["offer_acceptance"], reported_requirements=[req], decisions=[
        decide("c4", DecisionKind.verify_requirement, "c4_bgv", staff("hr", Role.desk_staff)),
    ])
    assert analyze(corporate, case).status == OutcomeStatus.needs_information


def test_invalid_rulepack_rejected(corporate):
    broken = corporate.model_copy(deep=True)
    broken.requirements.append(Requirement(id="bad", office="nowhere", produces="ghost", prerequisites="phantom"))
    with pytest.raises(RulePackError) as err:
        validate(broken)
    assert "unknown office" in str(err.value) and "unknown prerequisite" in str(err.value)
