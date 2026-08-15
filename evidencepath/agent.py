"""Transparent heuristic acquisition policies and a deterministic environment."""
from __future__ import annotations
from .models import CaseState, Action, Evidence, current_facts
from .logic import decision_snapshot
from .retrieval import rank_documents

DOC_COST = 1.0
ASK_COST = 3.0


def _unseen(state: CaseState):
    return [d for d in state.case.documents if d.id not in state.seen_documents]


def _document_option(state: CaseState, fact_key: str, retrieval_mode: str):
    ranked = rank_documents(state.case.keywords[fact_key], _unseen(state), mode=retrieval_mode)
    if not ranked:
        return None
    # Scores are nonzero only for lexical or LSA-similar matches.
    doc, score = ranked[0]
    return (doc, score) if score > 0 else None


def recommend_action(state: CaseState, strategy: str = "evidencepath", retrieval_mode: str = "hybrid") -> Action:
    snap = decision_snapshot(state)
    if snap["status"] != "UNRESOLVED":
        return Action("stop", None, None, "Every completion of the remaining unknown facts gives the same decision.", 0)
    _, conflicts = current_facts(state)
    unknown = [k for k in state.case.labels if k not in snap["known"]]
    critical = snap["critical"]
    if not unknown:
        return Action("stop", None, None, "No unobserved variables remain; manual review needed.", 0)

    if strategy == "generic-clarification":
        # Deliberately uninformed baseline: asks the first missing fact in case order.
        k = unknown[0]
        return Action("ask", k, None, "Generic clarification baseline: ask for the first unknown fact.", ASK_COST)

    if strategy == "retrieve-first":
        remaining = _unseen(state)
        if remaining:
            query = state.case.description + " " + state.case.policy_text
            ranked = rank_documents(query, remaining, mode=retrieval_mode)
            doc, score = ranked[0]
            return Action("retrieve", None, doc.id, "Retrieve-first baseline: search broadly before asking the supplier.", DOC_COST, score)
        k = (critical or unknown)[0]
        return Action("ask", k, None, "Documents exhausted; request a missing fact from supplier.", ASK_COST)

    if strategy != "evidencepath":
        raise ValueError(f"Unknown strategy: {strategy}")
    # Strong invariant: conflicting evidence is not resolved by majority vote.
    for k in critical:
        if k in conflicts:
            return Action("ask", k, None, "Conflicting sources cannot establish this decision-critical fact; request reconciliation.", ASK_COST)

    # Cost-aware choice: prefer an accessible relevant source over a supplier query.
    # The planner sees only textual retrieval scores, never hidden supplier truths.
    for k in critical:
        opt = _document_option(state, k, retrieval_mode)
        if opt:
            doc, score = opt
            return Action("retrieve", k, doc.id,
                          f"'{state.case.labels[k]}' can change the decision. Search this likely source before asking the supplier (document cost {DOC_COST:g} vs clarification {ASK_COST:g}).",
                          DOC_COST, score)
    k = critical[0] if critical else unknown[0]
    return Action("ask", k, None, f"'{state.case.labels[k]}' can change the decision; no unexamined relevant document remains. Request clarification.", ASK_COST)


def execute_action(state: CaseState, action: Action) -> dict:
    """Execute one step. Supplier answers are revealed here, never during planning."""
    snap_before = decision_snapshot(state)
    detail: list[str] = []
    if action.kind == "stop":
        event = {"step":len(state.trace)+1,"action":"Stop","target":"—","source":"—","cost":0.0,"observed":"No additional evidence needed","reason":action.reason,"status":snap_before["status"]}
        state.trace.append(event)
        return event

    if action.kind == "retrieve":
        doc = next(d for d in state.case.documents if d.id == action.document_id)
        if doc.id in state.seen_documents:
            raise ValueError("Cannot retrieve the same document twice")
        state.seen_documents.append(doc.id)
        state.searches += 1
        for key, val in doc.assertions.items():
            state.evidence.setdefault(key, []).append(Evidence(val, doc.title, doc.id))
            detail.append(f"{state.case.labels[key]}: {'Yes' if val else 'No'}")
        source, target = doc.title, state.case.labels.get(action.target, "Broad retrieval")
    elif action.kind == "ask":
        key = action.target
        if key not in state.case.supplier_answers:
            raise ValueError(f"No simulator answer for {key}")
        val = state.case.supplier_answers[key]
        state.resolved[key] = val  # Explicitly reconciles conflicting document statements.
        state.evidence.setdefault(key, []).append(Evidence(val, "Simulated supplier clarification"))
        state.questions += 1
        detail = [f"{state.case.labels[key]}: {'Yes' if val else 'No'}"]
        source, target = "Simulated supplier", state.case.labels[key]
    else:
        raise ValueError(f"Unsupported action: {action.kind}")
    state.cost += action.cost
    # Count steps that acquired no currently decision-critical fact, even when
    # a broad retrieval strategy does not name a target in advance.
    if action.kind == "retrieve" and not (set(doc.assertions) & set(snap_before["critical"])):
        state.unnecessary_actions += 1
    elif action.kind == "ask" and action.target not in snap_before["critical"]:
        state.unnecessary_actions += 1
    after = decision_snapshot(state)
    event = {"step":len(state.trace)+1,"action": "Search document" if action.kind=="retrieve" else "Ask supplier", "target":target,
             "source":source,"cost":action.cost,"observed":"; ".join(detail) if detail else "No structured facts extracted",
             "reason":action.reason,"status":after["status"]}
    state.trace.append(event)
    return event


def run_case(state: CaseState, strategy: str = "evidencepath", retrieval_mode: str = "hybrid", max_steps: int = 16):
    for _ in range(max_steps):
        action = recommend_action(state, strategy, retrieval_mode)
        if action.kind == "stop":
            break
        execute_action(state, action)
    return state
