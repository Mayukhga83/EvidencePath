"""Exact possible-worlds policy evaluator for small Boolean rule sets."""
from __future__ import annotations
from itertools import product
from .models import Rule, CaseState, current_facts


def variables(rule: Rule) -> set[str]:
    if rule["op"] == "fact":
        return {rule["key"]}
    if rule["op"] == "not":
        return variables(rule["arg"])
    if rule["op"] in ("and", "or"):
        out: set[str] = set()
        for x in rule["args"]:
            out |= variables(x)
        return out
    raise ValueError(f"Unknown rule op: {rule['op']}")


def evaluate(rule: Rule, assignment: dict[str, bool]) -> bool:
    op = rule["op"]
    if op == "fact":
        return assignment[rule["key"]]
    if op == "not":
        return not evaluate(rule["arg"], assignment)
    if op == "and":
        return all(evaluate(x, assignment) for x in rule["args"])
    if op == "or":
        return any(evaluate(x, assignment) for x in rule["args"])
    raise ValueError(f"Unknown rule op: {op}")


def possible_outcomes(rule: Rule, facts: dict[str, bool]) -> set[bool]:
    missing = sorted(variables(rule) - facts.keys())
    if len(missing) > 16:
        raise ValueError("Exact evaluator supports at most 16 unresolved policy variables")
    return {evaluate(rule, facts | dict(zip(missing, vals))) for vals in product((False, True), repeat=len(missing))}


def status(rule: Rule, facts: dict[str, bool]) -> str:
    outcomes = possible_outcomes(rule, facts)
    if len(outcomes) != 1:
        return "UNRESOLVED"
    return "ELIGIBLE" if True in outcomes else "NOT ELIGIBLE"


def critical_facts(rule: Rule, facts: dict[str, bool]) -> list[str]:
    """Facts which can change the decision under at least one consistent completion.

    In a multi-unknown conjunction, every unknown may be pivotal. If the
    decision is already invariant, no further fact is decision-critical.
    """
    if len(possible_outcomes(rule, facts)) == 1:
        return []
    candidates = sorted(variables(rule) - facts.keys())
    out = []
    for key in candidates:
        remaining = sorted(set(candidates) - {key})
        for vals in product((False, True), repeat=len(remaining)):
            partial = facts | dict(zip(remaining, vals))
            if evaluate(rule, partial | {key: False}) != evaluate(rule, partial | {key: True}):
                out.append(key)
                break
    return out


def decision_snapshot(state: CaseState) -> dict:
    facts, conflicts = current_facts(state)
    outcomes = possible_outcomes(state.case.rule, facts)
    return {
        "status": status(state.case.rule, facts),
        "known": facts,
        "conflicts": sorted(conflicts),
        "unknown": sorted(set(state.case.labels) - facts.keys()),
        "critical": critical_facts(state.case.rule, facts),
        "possible_outcomes": ["ELIGIBLE" if x else "NOT ELIGIBLE" for x in sorted(outcomes, reverse=True)],
    }
