"""Core types. The hidden supplier answers are only accessed by simulated clarification."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

Rule = dict[str, Any]


def fact(key: str) -> Rule:
    return {"op": "fact", "key": key}


def AND(*args: Rule) -> Rule:
    return {"op": "and", "args": list(args)}


def OR(*args: Rule) -> Rule:
    return {"op": "or", "args": list(args)}


def NOT(expr: Rule) -> Rule:
    return {"op": "not", "arg": expr}


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    # Pre-curated assertions stand in for a validated information-extraction layer.
    assertions: dict[str, bool]


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    description: str
    policy_text: str
    rule: Rule
    labels: dict[str, str]
    keywords: dict[str, str]
    initial: dict[str, bool]
    documents: tuple[Document, ...]
    # This ground truth is sealed off from the planner; the supplier simulator uses it.
    supplier_answers: dict[str, bool]
    category: str = "Supplier approval"
    preloaded_documents: tuple[str, ...] = ()


@dataclass
class Evidence:
    value: bool
    source: str
    document_id: str | None = None
    quote: str = ""
    location: str = ""
    method: str = "scenario / curated"
    verified: bool = False  # quote appears in source; NOT a truth guarantee


@dataclass
class CaseState:
    case: Case
    evidence: dict[str, list[Evidence]] = field(default_factory=dict)
    resolved: dict[str, bool] = field(default_factory=dict)
    seen_documents: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    cost: float = 0.0
    searches: int = 0
    questions: int = 0
    unnecessary_actions: int = 0


@dataclass(frozen=True)
class Action:
    kind: str  # retrieve | ask | stop
    target: str | None
    document_id: str | None
    reason: str
    cost: float
    retrieval_score: float = 0.0


def new_state(case: Case) -> CaseState:
    state = CaseState(case=case, evidence={k: [Evidence(v, "Initial scenario brief")] for k, v in case.initial.items()})
    for doc in case.documents:
        if doc.id in case.preloaded_documents:
            state.seen_documents.append(doc.id)
            for key, val in doc.assertions.items():
                state.evidence.setdefault(key, []).append(Evidence(val, doc.title, doc.id))
    return state


def current_facts(state: CaseState) -> tuple[dict[str, bool], set[str]]:
    """Return agreed facts and any unresolved source contradictions."""
    known = {}
    conflicts = set()
    for key, sources in state.evidence.items():
        if key in state.resolved:
            known[key] = state.resolved[key]
        elif sources:
            values = {ev.value for ev in sources}
            if len(values) == 1:
                known[key] = next(iter(values))
            else:
                conflicts.add(key)
    return known, conflicts
