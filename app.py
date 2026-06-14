from __future__ import annotations

import re
from uuid import uuid4

import pandas as pd
import streamlit as st

from graphmind.config import settings
from graphmind.models import MemoryCandidate
from graphmind.orchestrator import (
    apply_review_candidate,
    heuristic_intent,
    retrieve_agent,
    run_turn,
)
from graphmind.scenarios import SCENARIOS
from graphmind.storage import get_store
from graphmind.ui import (
    architecture_pipeline,
    creator_card,
    compact_memory_update,
    decision_cards,
    feature_card,
    graph_delta_panel,
    graph_figure,
    hero,
    inject_css,
    memory_cards,
    memory_table,
    scenario_header,
    trace_pipeline,
)

st.set_page_config(
    page_title="GraphMind Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


@st.cache_resource
def store_resource():
    return get_store()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def workspace_for(scenario_name: str, visitor_id: str) -> str:
    seed_version = SCENARIOS[scenario_name].get("seed_version", "v1")
    return f"{slug(scenario_name)}_{seed_version}_{visitor_id[:12]}"


def activate_scenario(scenario_name: str, reset: bool = False) -> None:
    workspace_id = workspace_for(scenario_name, st.session_state.visitor_id)
    store.clone_scenario(scenario_name, workspace_id, reset=reset)
    st.session_state.workspace_id = workspace_id
    st.session_state.latest_trace = None
    st.session_state.resolved_proposals = {}


def open_graph() -> None:
    st.session_state.nav_page = "Graph Explorer"


def relationship_time(memory: dict) -> str:
    """Return an ISO timestamp string suitable for newest-first sorting."""
    return str(memory.get("last_seen_at") or memory.get("first_seen_at") or "")


def sort_relationships_newest_first(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda memory: (
            relationship_time(memory),
            str(memory.get("first_seen_at") or ""),
            str(memory.get("id") or ""),
        ),
        reverse=True,
    )


def recent_update_memories(
    all_memories: list[dict],
    latest_trace: dict | None,
    fallback_limit: int = 10,
) -> list[dict]:
    """Return relationships changed by the latest turn, or the newest stored relationships."""
    delta = latest_trace.get("graph_delta", {}) if latest_trace else {}
    changed_ids = list(dict.fromkeys(delta.get("added_ids", []) + delta.get("updated_ids", [])))
    if changed_ids:
        changed = [memory for memory in all_memories if memory.get("id") in set(changed_ids)]
        return sort_relationships_newest_first(changed)
    return sort_relationships_newest_first(all_memories)[:fallback_limit]


def focused_graph_memories(
    all_memories: list[dict],
    selected_entity: str,
    include_second_hop: bool = False,
) -> list[dict]:
    """Return a readable one-hop or two-hop neighborhood around an entity."""
    one_hop = [
        memory
        for memory in all_memories
        if memory.get("subject") == selected_entity or memory.get("object") == selected_entity
    ]
    if not include_second_hop:
        return one_hop

    neighborhood = {selected_entity}
    for memory in one_hop:
        neighborhood.add(memory.get("subject"))
        neighborhood.add(memory.get("object"))
    return [
        memory
        for memory in all_memories
        if memory.get("subject") in neighborhood or memory.get("object") in neighborhood
    ]


store = store_resource()

if "visitor_id" not in st.session_state:
    st.session_state.visitor_id = uuid4().hex
if "scenario" not in st.session_state:
    st.session_state.scenario = "AI Researcher"
if "memory_mode" not in st.session_state:
    st.session_state.memory_mode = "Automatic"
if "workspace_id" not in st.session_state:
    activate_scenario(st.session_state.scenario)
if "latest_trace" not in st.session_state:
    st.session_state.latest_trace = None
if "resolved_proposals" not in st.session_state:
    st.session_state.resolved_proposals = {}
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Overview"

with st.sidebar:
    st.markdown("## ◈ GraphMind")
    st.caption("Visual agent memory")

    scenario = st.selectbox(
        "Scenario workspace",
        list(SCENARIOS),
        index=list(SCENARIOS).index(st.session_state.scenario),
    )
    if scenario != st.session_state.scenario:
        st.session_state.scenario = scenario
        activate_scenario(scenario)
        st.rerun()

    memory_mode = st.selectbox(
        "Memory policy",
        ["Automatic", "Review", "Observe only"],
        index=["Automatic", "Review", "Observe only"].index(st.session_state.memory_mode),
        help=(
            "Automatic writes safe high-confidence memories. Review lets you edit and approve proposals. "
            "Observe only shows what the system would remember without changing the graph."
        ),
    )
    st.session_state.memory_mode = memory_mode

    st.radio(
        "Navigation",
        ["Overview", "Memory Lab", "Graph Explorer", "Agent Trace", "Evaluation", "Memory Manager"],
        key="nav_page",
        label_visibility="collapsed",
    )

    st.divider()
    if st.button("Reset this workspace", use_container_width=True):
        activate_scenario(st.session_state.scenario, reset=True)
        st.rerun()
    if st.button("Create a fresh isolated copy", use_container_width=True):
        st.session_state.visitor_id = uuid4().hex
        activate_scenario(st.session_state.scenario)
        st.rerun()

    st.markdown("#### System")
    backend_label = "Supabase" if settings.backend_mode == "supabase" and settings.has_supabase else "Local JSON"
    st.caption(f"Storage · {backend_label}")
    st.caption(f"Model · {settings.openai_model if settings.has_openai else 'Deterministic demo fallback'}")
    st.caption(f"Session · {st.session_state.visitor_id[:8]}")

workspace_id = st.session_state.workspace_id
scenario_name = st.session_state.scenario
scenario_data = SCENARIOS[scenario_name]
memories = store.list_memories(workspace_id)
messages = store.list_messages(workspace_id)
traces = store.list_traces(workspace_id)
latest = st.session_state.latest_trace or (traces[-1] if traces else None)
if latest is not None and st.session_state.latest_trace is None:
    st.session_state.latest_trace = latest
page = st.session_state.nav_page

if page == "Overview":
    hero()
    
    st.write("")
    left, right = st.columns([1.55, 1])
    with left:
        st.subheader("A knowledge-graph-augmented hybrid memory framework for LLMs that evolves with the conversation")
        st.write(
            "GraphMind starts from a curated memory workspace (a person already interacted with the LLM), then updates memory from each new interaction in the Knowledge Graph. "
            "The framework retrieves relevant prior facts from both KG and vector memory before answering, extracts durable information from the "
            "latest conversation, resolves entity aliases, conversational references and conflicts."
        )
    with right:
        creator_card()

    st.write("")
    st.subheader("How to use the system")
    guide_columns = st.columns(5)
    guide = [
        ("Choose a scenario", "Select AI Researcher, Product Manager, or Travel Planner from the sidebar."),
        ("Send a message", "Open Memory Lab, choose an example message, or type your own in the input field."),
        ("See what was remembered", "Review the memories used and new information detected from your input."),
        ("View the graph change", "| Open Graph Explorer → Recent updates | to inspect the new or updated relationship."),
        ("Other Visualizations", "Explore Agent Orchestration Traces, Retrieval Evaluation and Memory Manager."),
    ]
    for index, (title, text) in enumerate(guide, start=1):
        with guide_columns[index - 1]:
            feature_card(title, text, f"STEP {index:02d}")


    st.write("")
    
    st.write("")
    metric_columns = st.columns(5)
    metric_columns[0].metric("Active memories", sum(m.get("status") in {"active", "confirmed"} for m in memories))
    metric_columns[1].metric("Graph entities", len({value for m in memories for value in [m["subject"], m["object"]]}))
    metric_columns[2].metric("Relationships", len(memories))
    metric_columns[3].metric("Conversation turns", len(messages) // 2)
    metric_columns[4].metric("Agent traces", len(traces))

elif page == "Memory Lab":
    st.title("Memory Lab")
    scenario_header(
        scenario_data.get("display_title", scenario_name),
        scenario_data["workspace"]["description"],
        scenario_data.get("scenario_tags", []),
        fictional=scenario_data.get("fictional_persona", False),
    )
    st.caption(
    "Continue the conversation naturally by choosing an example prompt or entering your own. "
    "Each turn retrieves relevant memories and may update the graph according to the selected memory policy."
    )

    prompt_columns = st.columns(3)
    for index, demo_prompt in enumerate(scenario_data["demo_prompts"][:3]):
        if prompt_columns[index].button(demo_prompt, use_container_width=True, key=f"demo_{index}"):
            st.session_state.queued_prompt = demo_prompt

    chat_column, context_column = st.columns([1.62, 1])
    submitted_prompt = None
    with chat_column:
        if not messages:
            st.info("This isolated workspace contains preset memory but no conversation yet. Start with a suggested prompt or write your own.")
        for message in messages[-16:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Keep the latest memory decision visually attached to the conversation turn
        # that produced it, instead of placing it far below the chat.
        latest_decisions = latest.get("new_memory_decisions", []) if latest else []
        if latest_decisions:
            compact_memory_update(latest_decisions)
            graph_changed = any(
                decision.get("persistence") in {"added", "updated"}
                for decision in latest_decisions
            )
            if graph_changed:
                st.button(
                    "View graph change",
                    on_click=open_graph,
                    use_container_width=True,
                    key="memory_lab_view_latest_graph",
                )

        typed_prompt = st.chat_input("Continue the conversation and teach the agent something durable...")
        submitted_prompt = typed_prompt or st.session_state.pop("queued_prompt", None)
        if submitted_prompt:
            with st.spinner("Running retrieval, response, extraction, conflict analysis, and memory update..."):
                answer, trace = run_turn(
                    store,
                    workspace_id,
                    submitted_prompt,
                    scenario_name,
                    st.session_state.memory_mode,
                )
                st.session_state.latest_trace = trace.model_dump()
            st.rerun()

    with context_column:
        st.subheader("Memory used for the answer")
        if latest:
            memory_cards(latest.get("retrieved_memories", []))
        else:
            st.info("Run a conversation turn to see the selected evidence.")
        st.subheader("Memory policy")
        policy_text = {
            "Automatic": "Safe, high-confidence memories are written immediately. Ambiguous or conflicting candidates wait for review.",
            "Review": "Every extracted candidate waits for approval and can be edited before it changes the graph.",
            "Observe only": "The pipeline runs fully, but no extracted memory is persisted.",
        }
        st.write(policy_text[st.session_state.memory_mode])

        if latest and latest.get("new_memory_decisions"):
            st.subheader("Latest memory decision")
            with st.expander("Why did the memory change?", expanded=False):
                decision_cards(latest.get("new_memory_decisions", []))

    if latest:
        st.divider()
        st.subheader("Agent orchestration")
        trace_pipeline(latest)

        st.subheader("Graph change from the latest turn")
        graph_delta_panel(latest.get("graph_delta", {}))

        pending = [
            decision
            for decision in latest.get("new_memory_decisions", [])
            if decision.get("persistence") == "pending"
            and decision.get("proposal_id") not in st.session_state.resolved_proposals
        ]
        if pending:
            st.subheader("Review proposed memories")
            st.caption("Edit the normalized triple before approving it, or reject it without changing the graph.")
            for decision in pending:
                proposal_id = decision["proposal_id"]
                candidate = decision["candidate"]
                with st.expander(
                    f"{candidate['subject']} → {candidate['relation']} → {candidate['object']}",
                    expanded=True,
                ):
                    with st.form(f"review_{proposal_id}"):
                        memory_type = st.selectbox(
                            "Memory type",
                            ["preference", "goal", "skill", "project", "constraint", "fact", "event"],
                            index=["preference", "goal", "skill", "project", "constraint", "fact", "event"].index(candidate["memory_type"]),
                        )
                        subject = st.text_input("Subject", candidate["subject"])
                        relation = st.text_input("Relation", candidate["relation"])
                        obj = st.text_input("Object", candidate["object"])
                        confidence = st.slider("Confidence", 0.0, 1.0, float(candidate["confidence"]), 0.01)
                        importance = st.slider("Importance", 0.0, 1.0, float(candidate["importance"]), 0.01)
                        evidence = st.text_area("Evidence", candidate.get("evidence", ""))
                        approve_column, reject_column = st.columns(2)
                        approve = approve_column.form_submit_button("Approve and update graph", use_container_width=True)
                        reject = reject_column.form_submit_button("Reject proposal", use_container_width=True)
                    if approve:
                        edited = MemoryCandidate(
                            memory_type=memory_type,
                            subject=subject,
                            relation=relation.upper().replace(" ", "_"),
                            object=obj,
                            confidence=confidence,
                            importance=importance,
                            evidence=evidence,
                        )
                        result = apply_review_candidate(
                            store,
                            workspace_id,
                            edited.model_dump(),
                            decision.get("source_message_id"),
                        )
                        st.session_state.resolved_proposals[proposal_id] = result["persistence"]
                        latest_decision = next(
                            row for row in st.session_state.latest_trace["new_memory_decisions"] if row["proposal_id"] == proposal_id
                        )
                        latest_decision.update(result)
                        delta = st.session_state.latest_trace["graph_delta"]
                        target = "updated_ids" if result["persistence"] == "updated" else "added_ids"
                        delta[target].append(result["memory_id"])
                        if proposal_id in delta.get("pending_ids", []):
                            delta["pending_ids"].remove(proposal_id)
                        refreshed = store.list_memories(workspace_id)
                        delta["after_memories"] = len(refreshed)
                        delta["after_entities"] = len({value for row in refreshed for value in [row["subject"], row["object"]]})
                        st.rerun()
                    if reject:
                        st.session_state.resolved_proposals[proposal_id] = "rejected"
                        latest_decision = next(
                            row for row in st.session_state.latest_trace["new_memory_decisions"] if row["proposal_id"] == proposal_id
                        )
                        latest_decision["persistence"] = "rejected"
                        delta = st.session_state.latest_trace["graph_delta"]
                        if proposal_id in delta.get("pending_ids", []):
                            delta["pending_ids"].remove(proposal_id)
                        st.rerun()

elif page == "Graph Explorer":
    st.title("Graph Explorer")
    scenario_header(
        scenario_data.get("display_title", scenario_name),
        scenario_data["workspace"]["description"],
        scenario_data.get("scenario_tags", []),
        fictional=scenario_data.get("fictional_persona", False),
    )
    st.caption(
        "Inspect what changed most recently, focus on one entity and its neighborhood, or open the complete graph. "
        "New relationships are teal, confirmed or updated relationships are amber, and answer-grounding memories are blue."
    )

    delta = latest.get("graph_delta", {}) if latest else {}
    used_ids = {memory["id"] for memory in latest.get("retrieved_memories", [])} if latest else set()
    added_ids = set(delta.get("added_ids", []))
    updated_ids = set(delta.get("updated_ids", []))

    view_mode = st.radio(
        "Graph view",
        ["Recent updates", "Focused graph", "Full graph"],
        horizontal=True,
        index=0,
        help=(
            "Recent updates isolates the latest changed links. Focused graph shows a small entity neighborhood. "
            "Full graph is available for advanced inspection."
        ),
    )

    if view_mode == "Recent updates":
        view_memories = recent_update_memories(memories, latest)
        if latest and (added_ids or updated_ids):
            st.subheader("Latest graph update")
            graph_delta_panel(delta)
            newest_changed = sort_relationships_newest_first(view_memories)
            if newest_changed:
                newest = newest_changed[0]
                st.info(
                    f"Latest relationship: **{newest['subject']} → {newest['relation'].replace('_', ' ')} → {newest['object']}**"
                )
        else:
            st.info(
                "No relationship has been changed in this session yet. Showing the most recently observed stored relationships."
            )
    elif view_mode == "Focused graph":
        entities = sorted({value for memory in memories for value in [memory["subject"], memory["object"]]})
        latest_changed = recent_update_memories(memories, latest, fallback_limit=1)
        preferred_entity = latest_changed[0]["subject"] if latest_changed else scenario_data.get("persona_name")
        default_index = entities.index(preferred_entity) if preferred_entity in entities else 0
        control_columns = st.columns([1.4, 1])
        selected_entity = control_columns[0].selectbox("Focus entity", entities, index=default_index)
        include_second_hop = control_columns[1].toggle(
            "Include second-hop context",
            value=False,
            help="Add relationships connected to the selected entity's immediate neighbors.",
        )
        view_memories = focused_graph_memories(memories, selected_entity, include_second_hop)
        st.caption(
            f"Showing {'two-hop' if include_second_hop else 'one-hop'} relationships around **{selected_entity}**."
        )
    else:
        view_memories = memories
        st.warning(
            "The full graph can be dense. Use Recent updates or Focused graph for faster inspection of a new or changed relationship."
        )

    with st.expander("Advanced filters", expanded=False):
        type_options = sorted({memory["memory_type"] for memory in view_memories})
        status_options = sorted({memory.get("status", "active") for memory in view_memories})
        filter_columns = st.columns([1, 1, 1.3])
        selected_types = filter_columns[0].multiselect("Memory types", type_options, default=type_options)
        selected_statuses = filter_columns[1].multiselect("Statuses", status_options, default=status_options)
        entity_query = filter_columns[2].text_input("Search entity or relation")

    filtered = [
        memory
        for memory in view_memories
        if memory["memory_type"] in selected_types
        and memory.get("status", "active") in selected_statuses
        and (
            not entity_query
            or entity_query.lower() in f"{memory['subject']} {memory['relation']} {memory['object']}".lower()
        )
    ]

    projects = scenario_data.get("projects", [])
    component_names = {
        component
        for component_list in scenario_data.get("project_components", {}).values()
        for component in component_list
    }
    if projects:
        st.caption(
            "Node colors: gold = fictional researcher · violet = research project · "
            "teal = functional component · blue = concept or output"
        )

    if filtered:
        st.plotly_chart(
            graph_figure(
                filtered,
                used_ids=used_ids,
                added_ids=added_ids,
                updated_ids=updated_ids,
                project_names=set(projects),
                component_names=component_names,
                persona_name=scenario_data.get("persona_name"),
            ),
            use_container_width=True,
        )
    else:
        st.info("No relationships match the current graph view and filters.")

    st.subheader("Evidence inspector")
    ordered_relationships = sort_relationships_newest_first(filtered)
    if ordered_relationships:
        relationship_by_id = {memory["id"]: memory for memory in ordered_relationships}
        newest_id = ordered_relationships[0]["id"]
        selected_id = st.selectbox(
            "Select a relationship",
            [memory["id"] for memory in ordered_relationships],
            format_func=lambda memory_id: (
                f"{relationship_by_id[memory_id]['subject']} → "
                f"{relationship_by_id[memory_id]['relation']} → "
                f"{relationship_by_id[memory_id]['object']}"
            ),
            index=0,
            key=f"evidence_{view_mode}_{newest_id}",
        )
        edge = relationship_by_id[selected_id]
        metric_columns = st.columns(4)
        metric_columns[0].metric("Confidence", f"{float(edge.get('confidence', 0)):.2f}")
        metric_columns[1].metric("Importance", f"{float(edge.get('importance', 0)):.2f}")
        metric_columns[2].metric("Status", edge.get("status", "active"))
        metric_columns[3].metric("Observed", edge.get("mention_count", 1))
        st.write(edge.get("evidence", "No evidence recorded."))
        st.caption(f"First seen: {edge.get('first_seen_at', '—')} · Last seen: {edge.get('last_seen_at', '—')}")
    else:
        st.info("No relationships match the current view and filters.")


elif page == "Agent Trace":
    st.title("Agent Trace")
    st.caption("Inspect structured decisions and evidence without exposing private hidden reasoning.")
    if not latest:
        st.info("Run a conversation turn in Memory Lab first.")
    else:
        trace_pipeline(latest)
        st.write("")
        for stage in latest.get("stages", []):
            with st.expander(f"{stage['name']} · {stage.get('duration_ms', 0)} ms"):
                st.write(stage["summary"])
                st.json(stage.get("details", {}))
        st.subheader("Final memory context supplied to the response agent")
        st.code(latest.get("final_context", ""), language="text")
        st.subheader("Memory-write result")
        graph_delta_panel(latest.get("graph_delta", {}))
        decision_cards(latest.get("new_memory_decisions", []))

elif page == "Evaluation":
    st.title("Retrieval Evaluation")
    st.caption("Run the same query through vector-only, graph-only, and hybrid ranking policies.")
    query = st.text_input("Evaluation query", scenario_data["demo_prompts"][0])
    plan = heuristic_intent(query, scenario_name)
    modes = {
        "Vector only": retrieve_agent(query, memories, plan, limit=8, mode_override="vector"),
        "Graph only": retrieve_agent(query, memories, plan, limit=8, mode_override="graph"),
        "Hybrid": retrieve_agent(query, memories, plan, limit=8, mode_override="hybrid"),
    }
    tabs = st.tabs(list(modes))
    for tab, (mode_name, rows) in zip(tabs, modes.items()):
        with tab:
            frame = pd.DataFrame(
                [
                    {
                        "Memory": f"{row['subject']} → {row['relation']} → {row['object']}",
                        "Type": row["memory_type"],
                        "Semantic": row["semantic_score"],
                        "Graph": row["graph_score"],
                        "Final": row["final_score"],
                    }
                    for row in rows
                ]
            )
            st.dataframe(frame, use_container_width=True, hide_index=True)
            if not frame.empty:
                st.bar_chart(frame.set_index("Memory")[["Semantic", "Graph", "Final"]])
    st.info(
        "This page is an inspectable MVP diagnostic, not a scientific benchmark. A rigorous extension should add "
        "labeled relevance judgments and report Precision@k, Recall@k, MRR, relationship coverage, conflict-aware "
        "accuracy, and memory citation coverage."
    )

else:
    st.title("Memory Manager")
    st.caption("Review evidence and manually control the lifecycle of stored memories.")
    st.dataframe(memory_table(memories), use_container_width=True, hide_index=True)
    if memories:
        labels = {
            f"{memory['memory_type']} · {memory['subject']} → {memory['relation']} → {memory['object']}": memory
            for memory in memories
        }
        selected = labels[st.selectbox("Select memory", list(labels))]
        action_columns = st.columns(3)
        if action_columns[0].button("Confirm", use_container_width=True):
            store.update_memory_status(selected["id"], "confirmed")
            st.rerun()
        if action_columns[1].button("Archive", use_container_width=True):
            store.update_memory_status(selected["id"], "archived")
            st.rerun()
        if action_columns[2].button("Mark contradicted", use_container_width=True):
            store.update_memory_status(selected["id"], "contradicted")
            st.rerun()
        with st.expander("Full memory record"):
            st.json(selected)
