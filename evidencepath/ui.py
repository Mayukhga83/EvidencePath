"""PaperMind-aligned presentation components for EvidencePath.

Pure presentation code only. No agent, benchmark, or retrieval state is modified here.
"""
from __future__ import annotations

from html import escape

import streamlit as st

# Aligned with PaperMind's published local styles: white canvas, navy typography,
# muted blue accents, pale blue surfaces, outlined cards, generous spacing.
APP_CSS = r"""
<style>
:root {
  --pm-navy:#102a43;
  --pm-blue:#1f5f99;
  --pm-pale:#f3f7fb;
  --pm-border:#d8e3ee;
  --pm-text:#243b53;
  --pm-muted:#627d98;
}
.block-container{max-width:1180px;padding-top:2.2rem;padding-bottom:4rem;}
[data-testid="stSidebar"]{border-right:1px solid var(--pm-border);background:#fbfdff;}
[data-testid="stSidebar"] h3{color:var(--pm-navy);}
.pm-hero{padding:1.25rem 1.4rem 1.15rem;border:1px solid var(--pm-border);border-radius:16px;background:linear-gradient(135deg,#f8fbff 0%,#eef5fb 100%);margin-bottom:.72rem;}
.pm-kicker{font-size:.76rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--pm-blue);margin-bottom:.3rem;}
.pm-title{font-size:2.25rem;line-height:1.08;font-weight:780;color:var(--pm-navy);margin:0;}
.pm-subtitle{font-size:1.05rem;line-height:1.5;color:var(--pm-text);margin:.45rem 0 0;max-width:900px;}
.pm-methods{font-size:.77rem;line-height:1.55;font-weight:650;color:var(--pm-blue);margin-top:.65rem;letter-spacing:.01em;}
.pm-methods span{color:#a1b5c9;margin:0 .28rem;}
.pm-author-card{display:flex;align-items:center;gap:1rem;padding:.78rem 1rem;margin:0 0 .9rem;background:#fff;border:1px solid var(--pm-border);border-left:4px solid var(--pm-blue);border-radius:12px;box-shadow:0 1px 2px rgba(16,42,67,.035);}
.pm-author-label{flex-shrink:0;font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--pm-muted);}
.pm-author-details{display:flex;align-items:center;flex-wrap:wrap;gap:.35rem;font-size:.88rem;color:var(--pm-text);}
.pm-author-details strong{color:var(--pm-navy);}
.pm-author-details a{color:var(--pm-blue);text-decoration:none;font-weight:600;}
.pm-author-details a:hover{text-decoration:underline;}
.pm-author-divider{color:#9fb3c8;}
.pm-section-title{font-size:1.25rem;font-weight:720;color:var(--pm-navy);margin:.55rem 0 .15rem;}
.pm-section-copy{font-size:.92rem;color:var(--pm-muted);margin-bottom:.65rem;}
.pm-card{border:1px solid var(--pm-border);border-radius:14px;padding:1rem 1.05rem;background:#fff;box-shadow:0 1px 2px rgba(16,42,67,.035);}
.pm-card-title{font-weight:720;color:var(--pm-navy);margin-bottom:.28rem;}
.ep-source{margin:.5rem 0 .75rem;}
.ep-source-text{font-size:.87rem;line-height:1.5;color:var(--pm-text);white-space:pre-wrap;margin:.6rem 0;}
.pm-meta{font-size:.8rem;color:var(--pm-muted);}
.pm-field-label{font-size:.77rem;text-transform:uppercase;letter-spacing:.06em;color:var(--pm-muted);font-weight:700;margin-top:.65rem;}
.pm-field-value{font-size:.94rem;line-height:1.52;color:var(--pm-text);}
.pm-footer{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--pm-border);color:var(--pm-muted);font-size:.82rem;text-align:center;}
/* EvidencePath-specific patterns, using the same shared palette. */
.ep-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.7rem;margin:.85rem 0 1.2rem;}
.ep-summary-card{padding:.85rem .9rem;border:1px solid var(--pm-border);border-radius:12px;background:#fff;min-width:0;box-shadow:0 1px 2px rgba(16,42,67,.025);}
.ep-summary-label{font-size:.72rem;letter-spacing:.045em;font-weight:650;color:var(--pm-muted);margin-bottom:.4rem;}
.ep-summary-value{font-size:1.27rem;line-height:1.2;font-weight:750;color:var(--pm-navy);overflow-wrap:anywhere;}
.ep-summary-hint{font-size:.72rem;margin-top:.35rem;color:var(--pm-muted);}
.ep-panel{padding:1rem 1.05rem;border:1px solid var(--pm-border);border-left:4px solid var(--pm-blue);border-radius:12px;background:#f8fbff;margin:.35rem 0 .65rem;}
.ep-panel-title{font-weight:725;color:var(--pm-navy);font-size:1.03rem;margin:.3rem 0 .45rem;}
.ep-panel-reason{font-size:.94rem;line-height:1.55;color:var(--pm-text);}
.ep-overline{font-size:.71rem;color:var(--pm-blue);font-weight:750;letter-spacing:.10em;text-transform:uppercase;}
.ep-policy{padding:.9rem 1.05rem;border:1px solid var(--pm-border);border-radius:12px;background:var(--pm-pale);margin:.8rem 0;}
.ep-policy-label{font-size:.75rem;font-weight:730;text-transform:uppercase;letter-spacing:.06em;color:var(--pm-blue);margin-bottom:.38rem;}
.ep-policy-text{font-size:.93rem;line-height:1.55;color:var(--pm-text);}
.ep-detail{padding:.8rem 1rem;border:1px solid var(--pm-border);border-radius:12px;background:#fff;margin:.7rem 0;}
.ep-dot{display:inline-block;width:8px;height:8px;border-radius:100%;margin-right:.45rem;background:var(--pm-blue);vertical-align:middle;}
.ep-bullet-ok{background:#25866a;}
.ep-bullet-unknown{background:#c9943c;}
.ep-bullet-block{background:#b95958;}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--pm-border);border-radius:12px;padding:.65rem .85rem;}
[data-testid="stMetricLabel"]{color:var(--pm-muted);}
[data-testid="stMetricValue"]{color:var(--pm-navy);}
.stButton>button[kind="primary"]{border-radius:10px;font-weight:700;}
.stButton>button[kind="secondary"]{border-radius:10px;}
[data-testid="stDataFrame"]{border:1px solid var(--pm-border);border-radius:10px;overflow:hidden;}
[data-testid="stExpander"]{border-radius:10px;border-color:var(--pm-border);}
[data-testid="stTabs"] button[role="tab"]{font-weight:650;}
@media (max-width:800px){
 .ep-summary{grid-template-columns:repeat(2,minmax(0,1fr));}
 .block-container{padding-top:1.25rem;}
}
@media (max-width:640px){
 .pm-author-card{align-items:flex-start;flex-direction:column;gap:.35rem;}
 .pm-author-details{line-height:1.5;}
 .pm-hero{padding:1rem 1.05rem;}
 .pm-title{font-size:1.95rem;}
 .pm-subtitle{font-size:.96rem;}
}
</style>
"""


def render_header() -> None:
    st.markdown(
        '''<div class="pm-hero">
          <div class="pm-kicker">DOCUMENT INTELLIGENCE · RESEARCH WORKBENCH</div>
          <div class="pm-title">EvidencePath</div>
          <div class="pm-subtitle">Find the right evidence. Know when you have enough to decide.</div>
          <div class="pm-methods">Hybrid retrieval <span>·</span> Source-grounded claims <span>·</span> Decision-aware agents <span>·</span> Reproducible evaluation</div>
        </div>''',
        unsafe_allow_html=True,
    )


def render_author_card() -> None:
    # Matches the author treatment in the user's PaperMind source.
    st.markdown(
        '''<div class="pm-author-card">
          <div class="pm-author-label">Developed by</div>
          <div class="pm-author-details">
            <strong>Mayukh Das</strong>
            <span class="pm-author-divider">·</span>
            <span>TU Braunschweig</span>
            <span class="pm-author-divider">·</span>
            <a href="mailto:mayukh@ifis.cs.tu-bs.de">mayukh@ifis.cs.tu-bs.de</a>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )


def render_how_it_works() -> None:
    with st.expander("How EvidencePath works", expanded=False):
        st.markdown(
            """**1. Document Lab (new in V2)**  \nInspect real text from PDF/TXT/MD files with source-linked claims, contradictions and a manual clarification loop. Optional neural retrieval and LLM extraction can be enabled explicitly.\n\n**2. Select a supplier scenario**  
Choose a fictional supplier policy and the evidence currently available.

**3. Inspect the decision state**  
EvidencePath identifies known facts, unknowns, contradictions and conditions that could still change the result.

**4. Acquire evidence**  
Run the acquisition policy one action at a time or continue until a decision or a stopping condition is reached. The system can inspect a simulated document or ask the supplier.

**5. Trace the decision**  
Inspect the evidence inventory, policy graph and action trace to see exactly which information justified the outcome.

**6. Compare research baselines**  
Use Benchmark Lab to compare acquisition cost, coverage and agent behaviour across synthetic scenarios.

*The original V1 synthetic lab and benchmark are unchanged. V2 Document Lab does not read curated assertions or hidden supplier answers. Offline patterns have limited coverage; neural retrieval and API extraction are opt-in. No part provides real compliance advice.*"""
        )


def render_section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="pm-section-title">{escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="pm-section-copy">{escape(subtitle)}</div>', unsafe_allow_html=True)


def render_policy(policy: str) -> None:
    st.markdown(
        f'<div class="ep-policy"><div class="ep-policy-label">Illustrative decision policy (not legal advice)</div><div class="ep-policy-text">{escape(policy)}</div></div>',
        unsafe_allow_html=True,
    )


def render_summary(status: str, known: int, total: int, critical: int, cost: float) -> None:
    items = [
        ("Current result", {"ELIGIBLE":"Meets the rule", "NOT ELIGIBLE":"Does not meet rule", "UNRESOLVED":"More evidence needed"}.get(status, status), "Based on information seen so far"),
        ("Facts checked", f"{known} / {total}", "Known answers in this case"),
        ("Decision-critical gaps", str(critical), "Missing facts that could change the result"),
        ("Evidence cost", f"{cost:g}", "Simulated effort points, not money"),
    ]
    cards = "".join(
        f'<div class="ep-summary-card"><div class="ep-summary-label">{escape(label)}</div>'
        f'<div class="ep-summary-value">{escape(value)}</div><div class="ep-summary-hint">{escape(hint)}</div></div>'
        for label, value, hint in items
    )
    st.markdown(f'<div class="ep-summary">{cards}</div>', unsafe_allow_html=True)


def render_action(title: str, reason: str) -> None:
    st.markdown(
        f'<div class="ep-panel"><div class="ep-overline">Agent recommendation</div>'
        f'<div class="ep-panel-title">{escape(title)}</div>'
        f'<div class="ep-panel-reason">{escape(reason)}</div></div>',
        unsafe_allow_html=True,
    )


def render_source_document(
    title: str, doc_id: str, inspected: bool, text: str, assertions: str
) -> None:
    state = "Inspected" if inspected else "Not yet inspected"
    details = (
        f'<div class="ep-source-text">{escape(text)}</div>'
        f'<div class="pm-meta"><strong>Curated assertions:</strong> {escape(assertions)}</div>'
        if inspected else
        '<div class="pm-meta" style="margin-top:.5rem">'
        'Contents become visible after an agent inspection. Assertions are pre-curated in source code.'
        '</div>'
    )
    st.markdown(
        f'<div class="pm-card ep-source"><div class="pm-card-title">{escape(title)}</div>'
        f'<div class="pm-meta">{escape(doc_id)} · {state}</div>{details}</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        '<div class="pm-footer">EvidencePath · Research demo · '
        'Example supplier rules · Results are not legal or security advice</div>',
        unsafe_allow_html=True,
    )

# V3 keeps the established PaperMind-aligned white/navy/blue visual system.
# Only the high-level navigation changes; original presentation primitives remain reusable.
