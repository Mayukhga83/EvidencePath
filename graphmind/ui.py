from __future__ import annotations

from html import escape
import math

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {max-width: 1280px; padding-top: 1.35rem; padding-bottom: 3rem;}
        [data-testid="stSidebar"] {border-right: 1px solid rgba(255,255,255,.08);}
        .gm-hero {padding: 2.25rem; border: 1px solid rgba(255,255,255,.09);
          border-radius: 24px; background: linear-gradient(135deg, rgba(62,92,190,.27), rgba(18,24,40,.76));}
        .gm-eyebrow {font-size:.75rem; letter-spacing:.14em; text-transform:uppercase; opacity:.72;}
        .gm-title {font-size:2.8rem; line-height:1.03; font-weight:760; margin:.38rem 0 .7rem;}
        .gm-subtitle {font-size:1.08rem; max-width:830px; opacity:.84; line-height:1.55;}
        .gm-card {padding:1.05rem 1.1rem; border:1px solid rgba(255,255,255,.09);
          background:rgba(255,255,255,.025); border-radius:18px; min-height:130px;}
        .gm-card.compact {min-height:104px;}
        .gm-step {font-size:.72rem; opacity:.62; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.38rem;}
        .gm-card-title {font-weight:720; font-size:1.02rem; margin-bottom:.35rem;}
        .gm-card-text {font-size:.91rem; opacity:.77; line-height:1.45;}
        .gm-agent {padding:.85rem 1rem; border-left:3px solid #7184E8;
          background:rgba(78,99,190,.10); border-radius:12px; margin-bottom:.65rem; min-height:126px;}
        .gm-agent small {opacity:.75;}
        .gm-memory {padding:.72rem .82rem; border:1px solid rgba(255,255,255,.075);
          border-radius:12px; margin-bottom:.46rem; background:rgba(255,255,255,.018);}
        .gm-update-compact {padding:.78rem .9rem; border:1px solid rgba(77,214,200,.34);
          border-left:3px solid #4DD6C8; border-radius:13px; margin:.7rem 0 .45rem;
          background:linear-gradient(135deg, rgba(77,214,200,.10), rgba(31,42,70,.32));}
        .gm-update-compact.pending {border-color:rgba(240,182,91,.34); border-left-color:#F0B65B;
          background:linear-gradient(135deg, rgba(240,182,91,.09), rgba(31,42,70,.30));}
        .gm-update-compact.observed {border-color:rgba(141,155,255,.34); border-left-color:#8D9BFF;
          background:linear-gradient(135deg, rgba(141,155,255,.09), rgba(31,42,70,.30));}
        .gm-update-title {font-size:.82rem; font-weight:720; margin-bottom:.34rem;}
        .gm-update-triple {font-size:.93rem; line-height:1.4;}
        .gm-update-detail {font-size:.78rem; opacity:.70; margin-top:.28rem;}
        .gm-update {padding:.9rem 1rem; border:1px solid rgba(255,255,255,.09);
          border-radius:14px; margin:.5rem 0; background:rgba(31,42,70,.38);}
        .gm-label {display:inline-block; padding:.22rem .5rem; border-radius:999px;
          border:1px solid rgba(255,255,255,.14); font-size:.70rem; letter-spacing:.04em; margin-right:.35rem;}
        .gm-creator {padding:1.1rem 1.15rem; border:1px solid rgba(255,255,255,.09);
          border-radius:18px; background:rgba(55,73,130,.10);}
        .gm-scenario {padding:1rem 1.1rem; border:1px solid rgba(255,255,255,.085);
          border-radius:17px; background:linear-gradient(135deg, rgba(67,83,145,.13), rgba(255,255,255,.018));
          margin:.25rem 0 1rem;}
        .gm-scenario-title {font-size:1.05rem; font-weight:720; margin:.15rem 0 .35rem;}
        .gm-scenario-text {font-size:.91rem; opacity:.78; line-height:1.45; max-width:900px;}
        .gm-scenario-tags {margin-top:.65rem;}
        .gm-pipeline {display:flex; gap:.45rem; align-items:stretch; flex-wrap:wrap;}
        .gm-pipe-node {flex:1 1 130px; min-width:130px; padding:.75rem; border-radius:13px;
          border:1px solid rgba(255,255,255,.08); background:rgba(255,255,255,.022); font-size:.83rem;}
        .gm-pipe-arrow {display:flex; align-items:center; opacity:.42;}
        div[data-testid="stMetric"] {border:1px solid rgba(255,255,255,.075); padding:.75rem; border-radius:15px;}
        a {text-decoration:none;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    st.markdown(
        """
        <div class="gm-hero">
          <div class="gm-eyebrow">Visual hybrid memory for LLMs through agent orchestration</div>
          <div class="gm-title">GraphMind Studio</div>
          <div class="gm-subtitle">
            Upload conversations and inspect how memories become structured relationships
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(title: str, text: str, step: str = "", compact: bool = False) -> None:
    compact_class = " compact" if compact else ""
    st.markdown(
        f'<div class="gm-card{compact_class}"><div class="gm-step">{escape(step)}</div>'
        f'<div class="gm-card-title">{escape(title)}</div>'
        f'<div class="gm-card-text">{escape(text)}</div></div>',
        unsafe_allow_html=True,
    )


def creator_card() -> None:
    st.markdown(
        """
        <div class="gm-creator">
          <div class="gm-step">Created by</div>
          <div class="gm-card-title">Mayukh Das</div>
          <div class="gm-card-text">TU Braunschweig<br>
          <a href="mailto:mayukh@ifis.cs.tu-bs.de">mayukh@ifis.cs.tu-bs.de</a></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def scenario_header(
    title: str,
    description: str,
    tags: list[str] | None = None,
    fictional: bool = False,
) -> None:
    labels = list(tags or [])
    if fictional:
        labels.insert(0, "Synthetic persona")
    tag_html = "".join(f'<span class="gm-label">{escape(tag)}</span>' for tag in labels)
    st.markdown(
        f'<div class="gm-scenario"><div class="gm-step">Selected scenario</div>'
        f'<div class="gm-scenario-title">{escape(title)}</div>'
        f'<div class="gm-scenario-text">{escape(description)}</div>'
        f'<div class="gm-scenario-tags">{tag_html}</div></div>',
        unsafe_allow_html=True,
    )


def architecture_pipeline() -> None:
    labels = [
        "User request",
        "Intent planning",
        "Hybrid retrieval",
        "Response composition",
        "Memory extraction",
        "Conflict analysis",
        "Graph update",
    ]
    pieces: list[str] = ['<div class="gm-pipeline">']
    for index, label in enumerate(labels):
        pieces.append(f'<div class="gm-pipe-node">{escape(label)}</div>')
        if index < len(labels) - 1:
            pieces.append('<div class="gm-pipe-arrow">→</div>')
    pieces.append("</div>")
    st.markdown("".join(pieces), unsafe_allow_html=True)


def memory_cards(rows: list[dict], max_items: int = 7) -> None:
    for memory in rows[:max_items]:
        score = memory.get("final_score", "—")
        st.markdown(
            f'<div class="gm-memory"><div class="gm-step">{escape(memory.get("memory_type", "fact").upper())} '
            f'· score {score}</div><strong>{escape(memory.get("subject", ""))}</strong> '
            f'→ {escape(memory.get("relation", "").replace("_", " "))} → '
            f'<strong>{escape(memory.get("object", ""))}</strong></div>',
            unsafe_allow_html=True,
        )


def trace_pipeline(trace: dict) -> None:
    stages = trace.get("stages", [])
    if not stages:
        st.info("Run a conversation turn to populate the orchestration trace.")
        return
    for start in range(0, len(stages), 4):
        batch = stages[start : start + 4]
        columns = st.columns(4)
        for column, stage in zip(columns, batch):
            with column:
                st.markdown(
                    f'<div class="gm-agent"><div class="gm-step">{escape(stage.get("status", "completed"))}</div>'
                    f'<strong>{escape(stage["name"])}</strong><br>'
                    f'<small>{escape(stage["summary"])}</small><br><br>'
                    f'<span class="gm-label">{stage.get("duration_ms", 0)} ms</span></div>',
                    unsafe_allow_html=True,
                )


def graph_delta_panel(delta: dict) -> None:
    columns = st.columns(4)
    columns[0].metric("New relationships", len(delta.get("added_ids", [])))
    columns[1].metric("Confirmed / updated", len(delta.get("updated_ids", [])))
    columns[2].metric("Pending review", len(delta.get("pending_ids", [])))
    entity_change = int(delta.get("after_entities", 0)) - int(delta.get("before_entities", 0))
    columns[3].metric("Entity change", f"{entity_change:+d}")


def compact_memory_update(decisions: list[dict]) -> None:
    """Render a concise, high-attention summary next to the latest chat turn."""
    if not decisions:
        return

    priority = {"updated": 0, "added": 1, "pending": 2, "observed": 3, "rejected": 4}
    ordered = sorted(
        decisions,
        key=lambda row: priority.get(str(row.get("persistence", "observed")), 9),
    )
    row = ordered[0]
    candidate = row.get("candidate", {})
    decision = row.get("decision", {})
    persistence = str(row.get("persistence", "observed")).lower()
    relationship = str(decision.get("relationship", "new")).replace("_", " ").title()

    if persistence in {"added", "updated"}:
        title = "Memory updated"
        css_state = ""
    elif persistence == "pending":
        title = "Memory proposed for review"
        css_state = " pending"
    elif persistence == "rejected":
        title = "Memory proposal rejected"
        css_state = " observed"
    else:
        title = "Memory observed"
        css_state = " observed"

    extra_count = max(len(decisions) - 1, 0)
    extra_text = f" · {extra_count} more decision{'s' if extra_count != 1 else ''}" if extra_count else ""
    persistence_label = persistence.replace("_", " ").title()

    st.markdown(
        f'<div class="gm-update-compact{css_state}">'
        f'<div class="gm-update-title">{escape(title)} '
        f'<span class="gm-label">{escape(persistence_label)}</span>'
        f'<span class="gm-label">{escape(relationship)}</span></div>'
        f'<div class="gm-update-triple"><strong>{escape(candidate.get("subject", ""))}</strong> → '
        f'{escape(candidate.get("relation", "").replace("_", " "))} → '
        f'<strong>{escape(candidate.get("object", ""))}</strong></div>'
        f'<div class="gm-update-detail">The full decision and explanation are available in the memory panel{escape(extra_text)}.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def decision_cards(decisions: list[dict]) -> None:
    if not decisions:
        st.caption("No durable memory was extracted from this turn.")
        return
    for row in decisions:
        candidate = row.get("candidate", {})
        decision = row.get("decision", {})
        persistence = row.get("persistence", "observed")
        st.markdown(
            f'<div class="gm-update"><span class="gm-label">{escape(persistence.upper())}</span>'
            f'<span class="gm-label">{escape(decision.get("relationship", "new").upper())}</span><br><br>'
            f'<strong>{escape(candidate.get("subject", ""))}</strong> → '
            f'{escape(candidate.get("relation", "").replace("_", " "))} → '
            f'<strong>{escape(candidate.get("object", ""))}</strong><br>'
            f'<small>{escape(decision.get("explanation", ""))}</small></div>',
            unsafe_allow_html=True,
        )


def graph_figure(
    memories: list[dict],
    used_ids: set[str] | None = None,
    added_ids: set[str] | None = None,
    updated_ids: set[str] | None = None,
    project_names: set[str] | None = None,
    component_names: set[str] | None = None,
    persona_name: str | None = None,
) -> go.Figure:
    used_ids = used_ids or set()
    added_ids = added_ids or set()
    updated_ids = updated_ids or set()
    project_names = project_names or set()
    component_names = component_names or set()
    active = [memory for memory in memories if memory.get("status") != "archived"]
    if not active:
        return go.Figure()

    layout_graph = nx.Graph()
    for memory in active:
        layout_graph.add_edge(memory["subject"], memory["object"])
    position = nx.spring_layout(
        layout_graph,
        seed=42,
        k=1.45 / math.sqrt(max(len(layout_graph.nodes), 1)),
        iterations=90,
    )

    edge_traces: list[go.Scatter] = []
    annotations: list[dict] = []
    for memory in active:
        source, target = memory["subject"], memory["object"]
        x0, y0 = position[source]
        x1, y1 = position[target]
        memory_id = memory["id"]
        status = memory.get("status", "active")
        if memory_id in added_ids:
            color, width, dash = "#4DD6C8", 4.5, "solid"
        elif memory_id in updated_ids:
            color, width, dash = "#F0B65B", 4.2, "solid"
        elif memory_id in used_ids:
            color, width, dash = "#8D9BFF", 3.4, "solid"
        elif status in {"contradicted", "superseded"}:
            color, width, dash = "#D66B75", 2.0, "dash"
        elif status == "candidate":
            color, width, dash = "#A9AFBF", 1.8, "dot"
        else:
            color, width, dash = "rgba(165,178,218,.52)", 1.3 + float(memory.get("confidence", 0.8)), "solid"

        hover = (
            f"{source} → {memory['relation']} → {target}<br>"
            f"Type: {memory.get('memory_type', 'fact')}<br>"
            f"Confidence: {float(memory.get('confidence', 0.8)):.2f}<br>"
            f"Status: {status}"
        )
        edge_traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"width": width, "color": color, "dash": dash},
                hoverinfo="text",
                text=[hover, hover],
                showlegend=False,
            )
        )
        annotations.append(
            dict(
                x=(x0 + x1) / 2,
                y=(y0 + y1) / 2,
                text=memory["relation"].replace("_", " "),
                showarrow=False,
                font={"size": 9, "color": "rgba(225,230,245,.72)"},
                bgcolor="rgba(15,18,26,.62)",
                borderpad=2,
            )
        )

    node_x, node_y, labels, sizes, hover, node_colors, line_colors = [], [], [], [], [], [], []
    for node in layout_graph.nodes:
        x, y = position[node]
        node_x.append(x)
        node_y.append(y)
        labels.append(node)
        degree = layout_graph.degree(node)
        sizes.append(21 + degree * 4 if node in project_names else 18 + degree * 4)
        if persona_name and node == persona_name:
            node_kind, node_color, line_color = "fictional researcher", "#D7A95B", "#FFE0A3"
        elif node in project_names:
            node_kind, node_color, line_color = "research project", "#7559C8", "#CFC1FF"
        elif node in component_names:
            node_kind, node_color, line_color = "functional component", "#2E9C9A", "#A9F0E9"
        else:
            node_kind, node_color, line_color = "concept or output", "#5269BE", "#AEBBFF"
        node_colors.append(node_color)
        line_colors.append(line_color)
        hover.append(f"{node}<br>{node_kind}<br>{degree} connected entities")
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=labels,
        textposition="top center",
        marker={"size": sizes, "color": node_colors, "line": {"width": 1.2, "color": line_colors}},
        hovertext=hover,
        hoverinfo="text",
        showlegend=False,
    )

    figure = go.Figure(data=edge_traces + [node_trace])
    figure.update_layout(
        height=625,
        margin={"l": 10, "r": 10, "t": 28, "b": 10},
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=annotations,
        hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def memory_table(memories: list[dict]) -> pd.DataFrame:
    columns = [
        "id",
        "memory_type",
        "subject",
        "relation",
        "object",
        "confidence",
        "importance",
        "status",
        "mention_count",
        "evidence",
        "first_seen_at",
        "last_seen_at",
    ]
    return pd.DataFrame([{column: memory.get(column) for column in columns} for memory in memories])
