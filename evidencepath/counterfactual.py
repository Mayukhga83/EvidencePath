"""Exact, transparent what-if reasoning for small propositional policy rules.

A what-if is hypothetical: it does not rewrite source evidence or the active case.
"""
from __future__ import annotations
from .logic import possible_outcomes, variables
from .models import CaseState, current_facts


def verdict(rule, facts: dict[str, bool]) -> str:
    results = possible_outcomes(rule, facts)
    return "UNRESOLVED" if len(results) > 1 else "ELIGIBLE" if True in results else "NOT ELIGIBLE"


def alternatives(state: CaseState, key: str) -> dict:
    if key not in state.case.labels:
        raise ValueError("Unrecognised policy fact")
    known, conflicts = current_facts(state)
    # Counterfactual switches the named fact (and only that fact) even when
    # observed source statements disagree. This NEVER counts as new evidence.
    facts = {k: v for k, v in known.items() if k != key}
    true_outcome = verdict(state.case.rule, facts | {key: True})
    false_outcome = verdict(state.case.rule, facts | {key: False})
    return {
        "key": key,
        "fact": state.case.labels[key],
        "current": "CONFLICTED" if key in conflicts else "YES" if known.get(key) is True else "NO" if known.get(key) is False else "UNKNOWN",
        "if_yes": true_outcome,
        "if_no": false_outcome,
        "changes_decision": true_outcome != false_outcome,
        "in_rule": key in variables(state.case.rule),
        "other_unknowns_remaining": sorted(variables(state.case.rule) - (set(facts) | {key})),
    }
