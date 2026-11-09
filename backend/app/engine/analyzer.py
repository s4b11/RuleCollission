"""Deterministic route analysis over an AND/OR prerequisite graph.

The LLM never decides outcomes; it only proposes requirements. This module
decides, from recorded rules, case facts and authorised decisions, whether a
route exists, what blocks it, and which clarification or decision is needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import networkx as nx

from .models import (
    Alternative,
    Analysis,
    BlockingGroup,
    CandidateAlternative,
    Case,
    Clarification,
    Decision,
    DecisionKind,
    Expr,
    Note,
    OutcomeStatus,
    Requirement,
    Role,
    Route,
    RouteStatus,
    RouteStep,
    RulePack,
)


@dataclass(frozen=True)
class _Producer:
    id: str
    office: str
    produces: str
    prerequisites: Expr | None
    verified: bool
    alternative: str | None = None


@dataclass
class _Ctx:
    pack: RulePack
    case: Case
    notes: list[Note] = field(default_factory=list)
    clarifications: list[Clarification] = field(default_factory=list)
    resolved_terms: dict[str, str] = field(default_factory=dict)

    def note(self, kind: str, detail: str) -> None:
        if not any(n.kind == kind and n.detail == detail for n in self.notes):
            self.notes.append(Note(kind=kind, detail=detail))

    def ask(self, kind: str, about: str, office: str | None, question: str) -> None:
        if not any(c.kind == kind and c.about == about and c.target_office == office for c in self.clarifications):
            self.clarifications.append(Clarification(kind=kind, about=about, target_office=office, question=question))


# ---------- expression helpers ----------


def atoms(expr: Expr | None) -> list[str]:
    if expr is None:
        return []
    if isinstance(expr, str):
        return [expr]
    out: list[str] = []
    for key in ("all_of", "any_of"):
        for sub in expr.get(key, []):
            out.extend(atoms(sub))
    return out


def _evaluate(expr, office, reach, resolve, substitutes) -> list[str] | None:
    """Return the concrete documents used to satisfy expr, or None."""
    if expr is None:
        return []
    if isinstance(expr, str):
        doc = resolve(expr)
        options = [doc, *substitutes.get((doc, office), [])]
        available = [d for d in options if d in reach]
        if not available:
            return None
        return [min(available, key=lambda d: (reach[d], d != doc))]
    if "all_of" in expr:
        used: list[str] = []
        for sub in expr["all_of"]:
            part = _evaluate(sub, office, reach, resolve, substitutes)
            if part is None:
                return None
            used.extend(part)
        return used
    if "any_of" in expr:
        best: list[str] | None = None
        best_cost = None
        for sub in expr["any_of"]:
            part = _evaluate(sub, office, reach, resolve, substitutes)
            if part is None:
                continue
            cost = max((reach[d] for d in part), default=0)
            if best is None or cost < best_cost:
                best, best_cost = part, cost
        return best
    raise ValueError(f"Unsupported prerequisite expression: {expr!r}")


def _reach(producers, held, resolve, substitutes):
    reach: dict[str, int] = {d: 0 for d in held}
    chosen: dict[str, tuple[_Producer, list[str]]] = {}
    rnd = 0
    while True:
        rnd += 1
        new: dict[str, tuple[_Producer, list[str]]] = {}
        for p in producers:
            if p.produces in reach or p.produces in new:
                continue
            used = _evaluate(p.prerequisites, p.office, reach, resolve, substitutes)
            if used is not None:
                new[p.produces] = (p, used)
        if not new:
            return reach, chosen
        for doc, val in new.items():
            reach[doc] = rnd
            chosen[doc] = val


def _route_docs(goal: str, chosen) -> set[str]:
    needed: set[str] = set()
    stack = [goal]
    while stack:
        d = stack.pop()
        if d in needed or d not in chosen:
            continue
        needed.add(d)
        stack.extend(chosen[d][1])
    return needed


# ---------- context building ----------


def _in_effect(req: Requirement, on: date) -> bool:
    if req.effective_from and on < req.effective_from:
        return False
    if req.effective_until and on > req.effective_until:
        return False
    return True


def _applicable(ctx: _Ctx, req: Requirement) -> bool:
    cats = req.applies_to.get("applicant_category")
    if not cats:
        return True
    if ctx.case.applicant_category is None:
        ctx.ask(
            "applicability",
            req.id,
            None,
            f"Requirement '{req.id}' applies only to {', '.join(cats)}. Which applicant category does this case fall under?",
        )
        return True
    return ctx.case.applicant_category in cats


def _validate_decision(ctx: _Ctx, d: Decision, reported: dict[str, Requirement], alts: dict[str, Alternative], term_users) -> bool:
    by = d.by
    if d.case_id != ctx.case.id:
        ctx.note("rejected_decision", f"{d.id}: recorded for case '{d.case_id}', not this case")
        return False
    if d.valid_until and ctx.case.as_of > d.valid_until:
        ctx.note("expired_decision", f"{d.id}: expired on {d.valid_until.isoformat()}")
        return False
    if by.role == Role.applicant:
        ctx.note("rejected_decision", f"{d.id}: applicants cannot record institutional decisions")
        return False

    k = d.kind
    if k == DecisionKind.verify_requirement:
        req = reported.get(d.target)
        ok = req is not None and by.office == req.office and by.role in (Role.desk_staff, Role.approver)
        reason = "only staff of the issuing office can verify its requirement"
    elif k in (DecisionKind.approve_alternative, DecisionKind.refuse_alternative):
        alt = alts.get(d.target)
        ok = alt is not None and by.role == Role.approver and by.office == alt.approval_by
        reason = f"only an approver from '{alt.approval_by if alt else '?'}' can decide this alternative"
    elif k == DecisionKind.accept_alternative:
        alt = alts.get(d.target)
        ok = alt is not None and by.role == Role.approver and by.office in alt.in_offices
        reason = "only an approver from an affected office can accept this alternative"
    else:
        term = d.target.split("=", 1)[0]
        ok = "=" in d.target and by.role == Role.approver and by.office in term_users.get(term, set())
        reason = "only an approver from an office using this term can confirm its meaning"
    if not ok:
        ctx.note("rejected_decision", f"{d.id}: {by.staff_id} ({by.role.value}, {by.office}) lacks authority; {reason}")
    return ok


def analyze(pack: RulePack, case: Case) -> Analysis:
    ctx = _Ctx(pack=pack, case=case)
    on = case.as_of
    doc_ids = {d.id for d in pack.documents}
    doc_names = {d.id: d.name for d in pack.documents}
    pack_aliases = {a: d.id for d in pack.documents for a in d.aliases}
    pack_rules = {r.id: r for r in pack.requirements}
    alts = {a.id: a for a in pack.alternatives}

    # Effective requirement set: approved rules in force, overridden by case-reported claims.
    reported: dict[str, Requirement] = {}
    for r in case.reported_requirements:
        if r.cites_rule and r.cites_rule in pack_rules and not _in_effect(pack_rules[r.cites_rule], on):
            current = [p.id for p in pack.requirements if p.office == r.office and p.produces == r.produces and _in_effect(p, on)]
            ctx.note(
                "version_mismatch",
                f"{r.id}: instruction follows rule '{r.cites_rule}', which is not in force on {on.isoformat()}; "
                f"current rule: {', '.join(current) or 'none'}",
            )
            continue
        if _applicable(ctx, r):
            reported[r.id] = r
    overridden = {(r.office, r.produces) for r in reported.values()}
    effective = [
        r for r in pack.requirements
        if _in_effect(r, on) and (r.office, r.produces) not in overridden and _applicable(ctx, r)
    ]

    term_users: dict[str, set[str]] = {}
    for r in [*effective, *reported.values()]:
        for t in atoms(r.prerequisites):
            term_users.setdefault(t, set()).add(r.office)

    # Decisions.
    valid = [d for d in case.decisions if _validate_decision(ctx, d, reported, alts, term_users)]
    verified_ids = {d.target for d in valid if d.kind == DecisionKind.verify_requirement}
    approved = {d.target for d in valid if d.kind == DecisionKind.approve_alternative}
    refused = {d.target for d in valid if d.kind == DecisionKind.refuse_alternative}
    accepted: dict[str, set[str]] = {}
    for d in valid:
        if d.kind == DecisionKind.accept_alternative:
            accepted.setdefault(d.target, set()).add(d.by.office)
    confirmed_eq: dict[str, str] = {}
    rejected_eq: set[str] = set()
    for d in valid:
        term, _, doc = d.target.partition("=")
        if d.kind == DecisionKind.confirm_equivalence:
            confirmed_eq[term] = doc
        elif d.kind == DecisionKind.reject_equivalence:
            rejected_eq.add(term)
    for a in refused:
        ctx.note("refused_alternative", f"{a}: refused by an authorised approver")

    def resolve(term: str) -> str:
        if term in doc_ids:
            return term
        if term in pack_aliases:
            ctx.note("equivalence_applied", f"'{term}' is an approved alias of '{pack_aliases[term]}'")
            return pack_aliases[term]
        if term in confirmed_eq and term not in rejected_eq:
            ctx.note("equivalence_applied", f"'{term}' confirmed equivalent to '{confirmed_eq[term]}' for this case")
            return confirmed_eq[term]
        return term

    # Held documents.
    held: set[str] = set()
    for h in case.held:
        doc = resolve(h.document)
        if h.expires_on and on > h.expires_on:
            ctx.note("expired_document", f"'{doc}' expired on {h.expires_on.isoformat()} and must be obtained again")
        else:
            held.add(doc)

    goal = resolve(case.goal)
    if goal in held:
        ctx.note("already_held", f"The goal document '{goal}' is already held")
        return Analysis(case_id=case.id, goal=goal, status=OutcomeStatus.route_available,
                        route=Route(status=RouteStatus.confirmed, steps=[]), notes=ctx.notes)

    req_by_id = {r.id: r for r in [*effective, *reported.values()]}
    producers = [
        _Producer(r.id, r.office, r.produces, r.prerequisites, r.is_verified or r.id in verified_ids)
        for r in [*effective, *reported.values()]
    ]

    def alt_active(a: Alternative) -> bool:
        if a.id not in approved or a.id in refused:
            return False
        return all(o == a.approval_by or o in accepted.get(a.id, set()) for o in a.in_offices)

    def alt_producer(a: Alternative) -> _Producer:
        return _Producer(a.id, a.office, a.produces, a.prerequisites, True, alternative=a.id)

    def substitutes_for(active: list[Alternative]):
        subs: dict[tuple[str, str], list[str]] = {}
        for a in active:
            for o in a.in_offices:
                subs.setdefault((resolve(a.substitutes), o), []).append(a.produces)
        return subs

    active_alts = [a for a in pack.alternatives if alt_active(a)]
    reach, chosen = _reach(producers + [alt_producer(a) for a in active_alts], held, resolve, substitutes_for(active_alts))

    # Relevance graph: everything that could feed the goal.
    graph = nx.DiGraph()
    for p in producers:
        for t in atoms(p.prerequisites):
            graph.add_edge(resolve(t), p.produces)
    graph.add_node(goal)
    relevant = nx.ancestors(graph, goal) | {goal}
    relevant_reqs = [p for p in producers if p.produces in relevant]

    # Incompatible conditions on the same document attribute.
    conflicts: list[list[str]] = []
    by_attr: dict[tuple[str, str], dict[str, list[str]]] = {}
    for p in relevant_reqs:
        for c in req_by_id[p.id].conditions:
            by_attr.setdefault((resolve(c.document), c.attribute), {}).setdefault(c.equals, []).append(p.id)
    for (doc, attr), values in by_attr.items():
        if len(values) > 1:
            ids = sorted({i for v in values.values() for i in v})
            conflicts.append(ids)
            detail = "; ".join(f"{', '.join(v)} require {attr}={val}" for val, v in values.items())
            ctx.ask("condition_conflict", doc, None,
                    f"'{doc_names.get(doc, doc)}' cannot satisfy incompatible conditions ({detail}). "
                    f"Which condition applies to this case, and who can confirm it?")

    def ask_verify(ids) -> None:
        for rid in ids:
            r = req_by_id[rid]
            if r.is_verified or rid in verified_ids:
                continue
            prereq = ", ".join(atoms(r.prerequisites)) or "nothing"
            ctx.ask("verify_requirement", rid, r.office,
                    f"Please confirm: does {r.office} require {prereq} before issuing "
                    f"'{doc_names.get(r.produces, r.produces)}'? (reported via {r.source.kind.value})")

    if goal in reach:
        needed = _route_docs(goal, chosen)
        steps = []
        for doc in sorted(needed, key=lambda d: (reach[d], d)):
            p, _ = chosen[doc]
            steps.append(RouteStep(order=0, document=doc, offices=[p.office], requirement_ids=[p.id], via_alternative=p.alternative))
        for i, s in enumerate(steps, 1):
            s.order = i
        used_reqs = [s.requirement_ids[0] for s in steps if not s.via_alternative]
        unverified = [rid for rid in used_reqs if not (req_by_id[rid].is_verified or rid in verified_ids)]
        ask_verify(unverified)
        route = Route(
            status=RouteStatus.confirmed if not unverified and not conflicts else RouteStatus.suggested,
            steps=steps,
            unverified_requirements=unverified,
            alternatives_used=[s.via_alternative for s in steps if s.via_alternative],
        )
        status = OutcomeStatus.needs_decision if conflicts else OutcomeStatus.route_available
        return Analysis(case_id=case.id, goal=goal, status=status, route=route, condition_conflicts=conflicts,
                        clarifications=ctx.clarifications, notes=ctx.notes)

    # ---------- goal unreachable: explain why ----------
    block = nx.DiGraph()
    for p in relevant_reqs:
        if p.produces in reach:
            continue
        for t in atoms(p.prerequisites):
            d = resolve(t)
            if d not in reach:
                block.add_edge(d, p.produces, req=p.id)
    groups: list[BlockingGroup] = []
    for scc in nx.strongly_connected_components(block):
        if len(scc) < 2 and not any(block.has_edge(n, n) for n in scc):
            continue
        rids = sorted({data["req"] for u, v, data in block.edges(data=True) if u in scc and v in scc})
        groups.append(BlockingGroup(documents=sorted(scc), requirement_ids=rids,
                                    sources={rid: req_by_id[rid].source for rid in rids}))
    groups.sort(key=lambda g: g.documents)

    producible = {p.produces for p in producers} | {a.produces for a in pack.alternatives}
    claims = {c.term: c for c in case.alias_claims}
    missing: list[str] = []
    for p in relevant_reqs:
        for t in atoms(p.prerequisites):
            d = resolve(t)
            if d in reach or d in producible:
                continue
            if t in claims and t not in rejected_eq:
                c = claims[t]
                ctx.ask("unconfirmed_equivalence", t, c.office,
                        f"Will {c.office} accept '{doc_names.get(c.document, c.document)}' as the '{t}' it requested?")
            elif d not in missing:
                missing.append(d)
                ctx.ask("missing_document", d, p.office,
                        f"{p.office} asked for '{t}'. Which office issues it, or does the applicant already hold it?")

    # Would any approved-in-principle alternative unlock the goal?
    candidates: list[CandidateAlternative] = []
    open_alts = [a for a in pack.alternatives if a.id not in refused]
    h_reach, h_chosen = _reach(producers + [alt_producer(a) for a in open_alts], held, resolve, substitutes_for(open_alts))
    if goal in h_reach:
        used_alts = {h_chosen[d][0].alternative for d in _route_docs(goal, h_chosen)} - {None}
        for aid in sorted(used_alts):
            a = alts[aid]
            pending = [o for o in a.in_offices if o != a.approval_by and o not in accepted.get(aid, set())]
            candidates.append(CandidateAlternative(alternative_id=aid, approved=aid in approved, refused=False,
                                                   pending_acceptance_from=pending))
            if aid not in approved:
                ctx.ask("alternative_approval", aid, a.approval_by,
                        f"Does the approved alternative '{a.description or aid}' apply to this case? "
                        f"If so, what conditions and validity apply?")
            for o in pending:
                ctx.ask("alternative_acceptance", aid, o,
                        f"If '{a.produces}' is issued under '{aid}', will {o} accept it in place of '{a.substitutes}'?")

    for g in groups:
        ask_verify(g.requirement_ids)
    unverified_block = any(not (req_by_id[r].is_verified or r in verified_ids) for g in groups for r in g.requirement_ids)

    if candidates:
        status = OutcomeStatus.needs_decision
    elif missing or any(c.kind == "unconfirmed_equivalence" for c in ctx.clarifications) or unverified_block:
        status = OutcomeStatus.needs_information
    else:
        status = OutcomeStatus.unresolved
        offices = sorted({req_by_id[r].office for g in groups for r in g.requirement_ids})
        docs = sorted({d for g in groups for d in g.documents})
        ctx.ask("decision_request", ",".join(docs) or goal, None,
                f"Under the verified requirements, {', '.join(docs) or goal} each depend on one another and no approved "
                f"alternative applies. Decision needed from the process owner: can {', '.join(offices) or 'the offices'} "
                f"authorise a provisional document or joint processing for this case?")

    return Analysis(case_id=case.id, goal=goal, status=status, blocking_groups=groups, missing_documents=missing,
                    condition_conflicts=conflicts, candidate_alternatives=candidates,
                    clarifications=ctx.clarifications, notes=ctx.notes)
