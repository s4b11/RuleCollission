from datetime import date

import networkx as nx

from ..engine.analyzer import atoms
from ..engine.models import RulePack
from ..models import Case


def names(pack: RulePack) -> tuple[dict, dict]:
    documents = {d.id: d.name for d in pack.documents}
    offices = {o.id: o.name for o in pack.offices}
    return documents, offices


def case_summary(case: Case, pack: RulePack) -> dict:
    documents, offices = names(pack)
    analysis = case.analysis or {}
    route = analysis.get("route") or {}
    steps = [
        {
            "order": s["order"],
            "document": documents.get(s["document"], s["document"]),
            "office": offices.get(s["offices"][0], s["offices"][0]),
            "via_alternative": s.get("via_alternative"),
        }
        for s in route.get("steps", [])
    ]
    blockers = [
        {
            "documents": [documents.get(d, d) for d in group["documents"]],
            "requirements": group["requirement_ids"],
        }
        for group in analysis.get("blocking_groups", [])
    ]
    questions = [
        {"kind": r.kind, "office": offices.get(r.target_office, r.target_office), "question": r.question, "status": r.status}
        for r in case.reviews if r.status in ("open", "declined")
    ]
    return {
        "id": case.id,
        "code": case.code,
        "status": case.status,
        "goal": documents.get(case.goal, case.goal),
        "subject": case.subject.name,
        "held": [documents.get(d.document, d.document) for d in case.subject.documents],
        "steps": steps,
        "unverified_requirements": route.get("unverified_requirements", []),
        "blockers": blockers,
        "questions": questions,
        "notes": [n["detail"] for n in analysis.get("notes", [])],
    }


def in_force(rule, today: date) -> bool:
    return not (rule.effective_from and today < rule.effective_from) and not (
        rule.effective_until and today > rule.effective_until)


def case_graph(case: Case, pack: RulePack) -> dict:
    documents, offices = names(pack)
    aliases = {a: d.id for d in pack.documents for a in d.aliases}
    today = date.today()
    reported = [(r["office"], r["produces"], r.get("prerequisites")) for r in case.reported]
    overridden = {(office, produces) for office, produces, _ in reported}
    rules = reported + [
        (r.office, r.produces, r.prerequisites) for r in pack.requirements
        if in_force(r, today) and (r.office, r.produces) not in overridden
    ]
    graph = nx.DiGraph()
    graph.add_node(case.goal)
    for office, produces, prerequisites in rules:
        graph.add_node(produces, office=office)
        for term in atoms(prerequisites):
            graph.add_edge(aliases.get(term, term), produces)
    graph = graph.subgraph(nx.ancestors(graph, case.goal) | {case.goal})

    # Documents that wait on each other share a row, so a loop is easy to see.
    groups = nx.condensation(graph)
    row = {}
    for group in nx.topological_sort(groups):
        row[group] = max((row[before] + 1 for before in groups.predecessors(group)), default=0)

    analysis = case.analysis or {}
    held = {d.document for d in case.subject.documents}
    on_route = {s["document"] for s in (analysis.get("route") or {}).get("steps", [])}
    blocked = {d for group in analysis.get("blocking_groups", []) for d in group["documents"]}

    def state(doc: str) -> str:
        if doc in held:
            return "held"
        if doc in blocked:
            return "blocked"
        if doc in on_route:
            return "route"
        return "pending"

    nodes = [
        {
            "id": doc,
            "name": documents.get(doc, doc),
            "office": offices.get(graph.nodes[doc].get("office", ""), ""),
            "row": row[groups.graph["mapping"][doc]],
            "state": state(doc),
            "goal": doc == case.goal,
        }
        for doc in sorted(graph.nodes)
    ]
    return {"nodes": nodes, "edges": [{"from": a, "to": b} for a, b in graph.edges]}
