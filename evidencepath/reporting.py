"""Portable, text-only research audit exports (never writes uploaded docs to disk)."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from .document_lab import DocumentSession, ledger_rows
from .logic import decision_snapshot


def report_data(session: DocumentSession) -> dict:
    s = decision_snapshot(session.core)
    return {
        "product": "EvidencePath v0.3.3",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario": session.case.title,
        "policy_type": "Fictional illustrative internal policy",
        "policy": session.case.policy_text,
        "decision": s["status"],
        "possible_outcomes": s["possible_outcomes"],
        "known_facts": {session.case.labels[k]: v for k,v in s["known"].items()},
        "decision_critical_unknowns": [session.case.labels[k] for k in s["critical"]],
        "conflicts": [session.case.labels[k] for k in s["conflicts"]],
        "inspected_passages": len(session.inspected),
        "illustrative_acquisition_cost": session.cost,
        "evidence_ledger": ledger_rows(session),
        "agent_trace": list(session.events),
        "limitations": [
            "Not a legal or security determination, certification, or independently verified statement about a supplier.",
            "Source-grounded means a quote exists in a document; the quote may be false or outdated.",
            "Manual clarification is unverified and does not remove conflicting original evidence.",
            "Boolean policy model is illustrative and incomplete; omitted conditions can change real outcomes.",
        ],
    }


def report_json(session: DocumentSession) -> bytes:
    return json.dumps(report_data(session),indent=2,ensure_ascii=False).encode("utf-8")


def _esc_md(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def report_markdown(session: DocumentSession) -> bytes:
    data=report_data(session)
    lines=["# EvidencePath — Document review", "",f"**Scenario:** {data['scenario']}",
           f"**Decision:** {data['decision']}",f"**Date (UTC):** {data['generated_utc']}","",
           "## Example approval rule",data['policy'],"",
           "## Decision-critical missing facts"]
    lines += [f"- {label}" for label in data['decision_critical_unknowns']] or ["- No missing answer currently changes the result under this example rule"]
    lines += ["","## Evidence ledger (source-linked claims)","| Question | Answer | Document | Where | Document says |","|---|---|---|---|---|"]
    for r in data['evidence_ledger']:
        lines.append("| " + " | ".join(_esc_md(str(r.get(k,""))) for k in ('Fact','Value','Source','Location','Quote')) + " |")
    lines += ["", "## Agent execution trace"]
    for ev in data['agent_trace']:
        lines.append(f"- Step {ev['Step']}: {ev['Action']} — {ev['Target']} (status: {ev['Status']}; cost: {ev['Cost']})")
    lines += ["", "## What this report cannot prove"]
    lines += [f"- {x}" for x in data['limitations']]
    return ("\n".join(lines)+"\n").encode("utf-8")
