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


def case_graph(case: Case, pack: RulePack) -> dict:
    documents, offices = names(pack)
    aliases = {a: d.id for d in pack.documents for a in d.aliases}
    graph = nx.DiGraph()
    reported = [(r["office"], r["produces"], r.get("prerequisites")) for r in case.reported]
    overridden = {(office, produces) for office, produces, _ in reported}
    rules = reported + [
        (r.office, r.produces, r.prerequisites) for r in pack.requirements if (r.office, r.produces) not in overridden
    ]
    for office, produces, prerequisites in rules:
        graph.add_node(produces, office=office)
        for term in atoms(prerequisites):
            graph.add_edge(aliases.get(term, term), produces)
    if case.goal not in graph:
        graph.add_node(case.goal)

    relevant = nx.ancestors(graph, case.goal) | {case.goal}
    depth = nx.single_source_shortest_path_length(graph.reverse(), case.goal)
    deepest = max(depth.values(), default=0)
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
            "column": deepest - depth[doc],
            "state": state(doc),
            "goal": doc == case.goal,
        }
        for doc in sorted(relevant)
    ]
    edges = [{"from": a, "to": b} for a, b in graph.edges if a in relevant and b in relevant]
    return {"nodes": nodes, "edges": edges}
