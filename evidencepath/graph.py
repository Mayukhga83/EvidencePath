"""Construct a Graphviz/DOT evidence graph without external APIs."""
from __future__ import annotations
from .models import CaseState, Rule
from .logic import decision_snapshot


def _esc(s: str) -> str:
    return s.replace('\\','\\\\').replace('"','\\"').replace('\n',' ')


def to_dot(state: CaseState) -> str:
    snap = decision_snapshot(state)
    known, critical, conflicts = snap['known'],set(snap['critical']),set(snap['conflicts'])
    lines = [
        'digraph Evidence {', 'graph [rankdir=LR, bgcolor="transparent", pad="0.2", nodesep="0.25", ranksep="0.45"];',
        'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, color="#D8E3EE", fillcolor="#F8FBFF", fontcolor="#243B53"];',
        'edge [color="#9FB3C8", fontsize=9, fontname="Helvetica"];',
        'decision [label="Policy decision\\n'+_esc(snap['status'])+'", fillcolor="#E5F0FA", penwidth=1.3];',
    ]
    counter = [0]
    def visit(rule: Rule) -> str:
        counter[0]+=1
        nid='r'+str(counter[0])
        op=rule['op']
        if op == 'fact':
            key=rule['key']
            label=state.case.labels[key]
            val=('YES' if known[key] else 'NO') if key in known else ('CONFLICT' if key in conflicts else 'UNKNOWN')
            color='#E1F3EA' if key in known else ('#FCE2E2' if key in conflicts else '#FFF0D7' if key in critical else '#F3F7FB')
            lines.append(f'{nid} [label="{_esc(label)}\\n{val}", fillcolor="{color}"];')
            for j, ev in enumerate(state.evidence.get(key, [])):
                eid=f'e_{key}_{j}'
                lines.append(f'{eid} [label="{_esc(ev.source[:36])}", shape=note, fillcolor="#F5F5F5", fontsize=8];')
                lines.append(f'{eid} -> {nid} [label="{str(ev.value).lower()}"];')
        else:
            lines.append(f'{nid} [label="{op.upper()}", shape=diamond, fillcolor="#E7F0F8"];')
            children=rule.get('args',[rule['arg']] if op=='not' else [])
            for child in children:
                cid=visit(child)
                lines.append(f'{cid} -> {nid};')
        return nid
    top=visit(state.case.rule)
    lines.append(f'{top} -> decision;')
    lines.append('}')
    return '\n'.join(lines)
