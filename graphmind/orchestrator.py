from __future__ import annotations

import math
import re
import time
from uuid import uuid4

from pydantic import BaseModel, Field

from graphmind.config import settings
from graphmind.llm import structured_call, text_call
from graphmind.models import (
    AgentStage,
    AgentTrace,
    ConflictDecision,
    GraphDelta,
    IntentPlan,
    MemoryCandidate,
    MemoryItem,
    MemoryMode,
    Message,
    now_iso,
)
from graphmind.scenarios import SCENARIOS
from graphmind.storage import Store


class CandidateBatch(BaseModel):
    memories: list[MemoryCandidate] = Field(default_factory=list)


STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "is", "are", "was", "were", "i", "my", "me", "you", "your", "it", "this",
    "that", "be", "as", "at", "from", "by", "what", "should", "would", "could",
}


def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9+#.-]+", text.lower())
        if token not in STOPWORDS and len(token) > 1
    }


def entity_count(memories: list[dict]) -> int:
    return len({value for memory in memories for value in [memory["subject"], memory["object"]]})


def lexical_similarity(query: str, memory: dict) -> float:
    query_tokens = tokens(query)
    memory_tokens = tokens(
        " ".join(
            [
                memory.get("memory_type", ""),
                memory.get("subject", ""),
                memory.get("relation", ""),
                memory.get("object", ""),
                memory.get("evidence", ""),
            ]
        )
    )
    if not query_tokens or not memory_tokens:
        return 0.0
    return len(query_tokens & memory_tokens) / math.sqrt(len(query_tokens) * len(memory_tokens))


def graph_relevance(query: str, memory: dict, all_memories: list[dict]) -> float:
    query_tokens = tokens(query)
    direct_tokens = tokens(f"{memory.get('subject', '')} {memory.get('object', '')}")
    if query_tokens & direct_tokens:
        return 1.0

    neighbor_tokens: set[str] = set()
    subject = memory.get("subject", "").lower()
    obj = memory.get("object", "").lower()
    for other in all_memories:
        if other.get("id") == memory.get("id"):
            continue
        endpoints = [other.get("subject", "").lower(), other.get("object", "").lower()]
        if subject in endpoints or obj in endpoints:
            neighbor_tokens |= tokens(f"{other.get('subject', '')} {other.get('object', '')}")
    return 0.6 if query_tokens & neighbor_tokens else 0.0


def heuristic_intent(query: str, scenario_name: str = "AI Researcher") -> IntentPlan:
    lower = query.lower()
    needed: list[str] = []
    if any(term in lower for term in ["prefer", "like", "style", "want"]):
        needed.append("preference")
    if any(term in lower for term in ["goal", "next", "plan", "project", "recommend"]):
        needed.extend(["goal", "project"])
    if any(term in lower for term in ["skill", "experience", "worked", "built"]):
        needed.extend(["skill", "project"])
    if any(term in lower for term in ["budget", "deadline", "constraint", "cloud", "deploy"]):
        needed.append("constraint")
    priorities = SCENARIOS[scenario_name]["memory_priorities"]
    return IntentPlan(
        intent="recommendation" if any(term in lower for term in ["recommend", "should", "next"]) else "general_assistance",
        needed_memory_types=list(dict.fromkeys(needed)) or priorities[:4],
        retrieval_mode="hybrid",
        query_entities=[],
    )


def intent_agent(query: str, scenario_name: str) -> IntentPlan:
    scenario = SCENARIOS[scenario_name]
    system = (
        "Classify a request for a long-term-memory agent. Decide which typed memories are useful "
        "and whether vector, graph, or hybrid retrieval is appropriate. Do not answer the request. "
        f"Scenario: {scenario_name}. Memory priorities: {scenario['memory_priorities']}."
    )
    return structured_call(IntentPlan, system, query) or heuristic_intent(query, scenario_name)


def retrieve_agent(
    query: str,
    memories: list[dict],
    plan: IntentPlan,
    limit: int = 7,
    mode_override: str | None = None,
) -> list[dict]:
    mode = (mode_override or plan.retrieval_mode).lower()
    rows: list[dict] = []
    for memory in memories:
        if memory.get("status") not in {"active", "confirmed"}:
            continue
        vector_score = lexical_similarity(query, memory)
        graph_score = graph_relevance(query, memory, memories)
        importance = float(memory.get("importance", 0.7))
        confidence = float(memory.get("confidence", 0.8))
        frequency = min(float(memory.get("mention_count", 1)) / 3.0, 1.0)
        type_bonus = 0.15 if memory.get("memory_type") in plan.needed_memory_types else 0.0

        if mode == "vector":
            final_score = 0.65 * vector_score + 0.15 * importance + 0.10 * confidence + 0.10 * frequency
        elif mode == "graph":
            final_score = 0.65 * graph_score + 0.15 * importance + 0.10 * confidence + 0.10 * frequency
        else:
            final_score = (
                0.35 * vector_score
                + 0.25 * graph_score
                + 0.15 * importance
                + 0.10 * confidence
                + 0.10 * frequency
                + type_bonus
            )

        enriched = dict(memory)
        enriched.update(
            semantic_score=round(vector_score, 3),
            graph_score=round(graph_score, 3),
            final_score=round(final_score, 3),
            retrieval_mode=mode,
        )
        rows.append(enriched)
    return sorted(rows, key=lambda row: row["final_score"], reverse=True)[:limit]


def conversation_window(messages: list[dict], current_user_text: str) -> str:
    recent = messages[-settings.conversation_context_turns :]
    lines = [f"{message['role'].upper()}: {message['content']}" for message in recent]
    lines.append(f"USER: {current_user_text}")
    return "\n".join(lines)


def extract_agent(
    user_text: str,
    history_window: str,
    scenario_name: str,
    related_memories: list[dict],
) -> list[MemoryCandidate]:
    scenario = SCENARIOS[scenario_name]
    persona_name = scenario.get("persona_name", "User")
    system = f"""
You are the Memory Extraction Agent for the {scenario_name} workspace.
Extract only durable information useful in future sessions.
Resolve references such as 'the second option' using the conversation window.
Normalize first-person statements from the current speaker to the canonical graph subject: {persona_name}.
Prefer these memory types: {scenario['memory_priorities']}.
Allowed types: preference, goal, skill, project, constraint, fact, event.
Use concise canonical entities and UPPER_SNAKE_CASE relations.
Do not store greetings, temporary filler, questions without durable information, or assistant claims as speaker facts.
Evidence must be grounded in the current user message.
""".strip()
    prompt = (
        f"CONVERSATION WINDOW:\n{history_window}\n\n"
        f"RELATED EXISTING MEMORIES:\n{related_memories[:6]}\n\n"
        f"CURRENT USER MESSAGE:\n{user_text}"
    )
    result = structured_call(CandidateBatch, system, prompt)
    if result:
        return result.memories

    # Deterministic fallback keeps the local no-key demo functional.
    patterns = [
        ("preference", persona_name, "PREFERS", r"(?:i now prefer|i prefer|i like|i enjoy|i love)\s+(.+)", 0.89),
        ("goal", persona_name, "HAS_GOAL", r"(?:i now want|i want(?: to)?|my goal is to|i need to)\s+(.+)", 0.90),
        ("skill", persona_name, "HAS_SKILL", r"(?:i know|i have experience with|i am skilled in)\s+(.+)", 0.85),
        ("project", persona_name, "WORKED_ON", r"(?:i built|i worked on|i created)\s+(.+)", 0.91),
        ("constraint", persona_name, "CONSTRAINED_BY", r"(?:it must|the project must|i need it to)\s+(.+)", 0.88),
    ]
    candidates: list[MemoryCandidate] = []
    for memory_type, subject, relation, pattern, confidence in patterns:
        match = re.search(pattern, user_text, re.IGNORECASE)
        if match:
            obj = match.group(1).strip(" .")[:160]
            candidates.append(
                MemoryCandidate(
                    memory_type=memory_type,
                    subject=subject,
                    relation=relation,
                    object=obj,
                    confidence=confidence,
                    importance=0.82,
                    evidence=user_text[:280],
                )
            )
    return candidates


def resolve_candidates(candidates: list[MemoryCandidate], memories: list[dict]) -> tuple[list[MemoryCandidate], list[dict]]:
    known_entities = {value for memory in memories for value in [memory.get("subject", ""), memory.get("object", "")] if value}
    aliases = {
        "kg": "Knowledge Graph",
        "knowledge graphs": "Knowledge Graph",
        "graph db": "Graph Database",
        "streamlit cloud": "Streamlit Community Cloud",
        "rag": "Retrieval-Augmented Generation",
        "supabase db": "Supabase",
        "neo4j database": "Neo4j",
    }
    resolved: list[MemoryCandidate] = []
    notes: list[dict] = []
    for original in candidates:
        candidate = original.model_copy(deep=True)
        before = {"subject": candidate.subject, "object": candidate.object}
        candidate.subject = aliases.get(candidate.subject.lower(), candidate.subject)
        candidate.object = aliases.get(candidate.object.lower(), candidate.object)
        for entity in known_entities:
            if entity.lower() == candidate.subject.lower():
                candidate.subject = entity
            if entity.lower() == candidate.object.lower():
                candidate.object = entity
        notes.append(
            {
                "before": before,
                "after": {"subject": candidate.subject, "object": candidate.object},
                "changed": before != {"subject": candidate.subject, "object": candidate.object},
            }
        )
        resolved.append(candidate)
    return resolved, notes


def conflict_agent(candidate: MemoryCandidate, memories: list[dict]) -> tuple[ConflictDecision, dict | None]:
    exact = next(
        (
            memory
            for memory in memories
            if memory.get("subject", "").lower() == candidate.subject.lower()
            and memory.get("relation") == candidate.relation
            and memory.get("object", "").lower() == candidate.object.lower()
        ),
        None,
    )
    if exact:
        return (
            ConflictDecision(
                relationship="duplicate",
                explanation="The same subject-relation-object memory already exists.",
                action="Confirm the existing memory and increase its observation count.",
                confidence=0.99,
            ),
            exact,
        )

    same_relation = [
        memory
        for memory in memories
        if memory.get("subject", "").lower() == candidate.subject.lower()
        and memory.get("relation") == candidate.relation
    ]
    if same_relation:
        system = (
            "Compare an existing durable memory with a new candidate. Classify the relationship as "
            "new, duplicate, refinement, complement, contradiction, or supersedes. Return a practical storage action."
        )
        prompt = f"EXISTING:\n{same_relation[:4]}\n\nNEW:\n{candidate.model_dump()}"
        decision = structured_call(ConflictDecision, system, prompt)
        if decision:
            return decision, same_relation[0]
        return (
            ConflictDecision(
                relationship="complement",
                explanation="The subject and relation match an existing memory, but the object adds another compatible detail.",
                action="Keep both memories unless a user review marks one obsolete.",
                confidence=0.74,
            ),
            same_relation[0],
        )

    return (
        ConflictDecision(
            relationship="new",
            explanation="No equivalent or directly competing memory was found.",
            action="Create a new active memory.",
            confidence=0.95,
        ),
        None,
    )


def context_text(memories: list[dict]) -> str:
    if not memories:
        return "No relevant long-term memories were retrieved."
    return "\n".join(
        f"- [{memory.get('memory_type', 'fact')}] {memory.get('subject')} — "
        f"{memory.get('relation')} → {memory.get('object')} "
        f"(confidence {float(memory.get('confidence', 0.8)):.2f}; "
        f"evidence: {memory.get('evidence', '')[:140]})"
        for memory in memories
    )


def response_agent(
    query: str,
    memory_context: str,
    history_window: str,
    scenario_name: str,
) -> str:
    scenario = SCENARIOS[scenario_name]
    system = f"""
You are GraphMind Studio operating in the {scenario_name} scenario.
{scenario['role_prompt']}
Use only relevant stored memories as personal facts. Do not invent history.
Answer the current request directly, then briefly identify the remembered goals, constraints, or preferences that shaped the answer.
""".strip()
    prompt = (
        f"RECENT CONVERSATION:\n{history_window}\n\n"
        f"RETRIEVED LONG-TERM MEMORY:\n{memory_context}\n\n"
        f"CURRENT REQUEST:\n{query}"
    )
    result = text_call(system, prompt)
    if result:
        return result
    if scenario_name == "AI Researcher":
        return (
            "I have considered Lena's existing education, interests, preferences, and research context. "
            "This new information can be connected to the relevant memories and used naturally in later conversations."
        )
    if scenario_name == "Product Manager":
        return (
            "I have considered the existing customer priorities, roadmap decisions, and delivery constraints. "
            "This update can now shape later planning conversations."
        )
    return (
        "I have considered the stored travel preferences, companions, budget, and changing plans. "
        "This update can now be used in later recommendations."
    )


def _persist_candidate(
    store: Store,
    workspace_id: str,
    candidate: MemoryCandidate,
    decision: ConflictDecision,
    existing: dict | None,
    source_message_id: str | None,
) -> tuple[str, str]:
    if decision.relationship == "duplicate" and existing:
        item = MemoryItem.model_validate(existing)
        item.mention_count += 1
        item.last_seen_at = now_iso()
        item.confidence = max(item.confidence, candidate.confidence)
        item.importance = max(item.importance, candidate.importance)
        item.status = "confirmed"
        store.upsert_memory(item)
        return item.id, "updated"

    status = "active"
    if decision.relationship in {"contradiction", "supersedes"}:
        status = "candidate"
    item = MemoryItem(
        workspace_id=workspace_id,
        source_message_id=source_message_id,
        status=status,
        **candidate.model_dump(),
    )
    store.upsert_memory(item)
    return item.id, "added"


def apply_review_candidate(
    store: Store,
    workspace_id: str,
    candidate_payload: dict,
    source_message_id: str | None = None,
) -> dict:
    candidate = MemoryCandidate.model_validate(candidate_payload)
    current_memories = store.list_memories(workspace_id)
    resolved, _ = resolve_candidates([candidate], current_memories)
    candidate = resolved[0]
    decision, existing = conflict_agent(candidate, current_memories)
    memory_id, persistence = _persist_candidate(
        store, workspace_id, candidate, decision, existing, source_message_id
    )
    return {
        "candidate": candidate.model_dump(),
        "decision": decision.model_dump(),
        "memory_id": memory_id,
        "persistence": persistence,
    }


def run_turn(
    store: Store,
    workspace_id: str,
    query: str,
    scenario_name: str,
    memory_mode: MemoryMode = "Automatic",
) -> tuple[str, AgentTrace]:
    stages: list[AgentStage] = []
    existing_memories = store.list_memories(workspace_id)
    previous_messages = store.list_messages(workspace_id)
    history = conversation_window(previous_messages, query)
    before_memory_count = len(existing_memories)
    before_entity_count = entity_count(existing_memories)

    started = time.perf_counter()
    plan = intent_agent(query, scenario_name)
    stages.append(
        AgentStage(
            name="Intent Agent",
            summary=f"{plan.intent} · {plan.retrieval_mode} retrieval",
            details=plan.model_dump(),
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    )

    started = time.perf_counter()
    retrieved = retrieve_agent(query, existing_memories, plan)
    stages.append(
        AgentStage(
            name="Hybrid Retrieval Agent",
            summary=f"Selected {len(retrieved)} memories from {len(existing_memories)} candidates",
            details={
                "selected": [
                    {
                        "memory": f"{m['subject']} → {m['relation']} → {m['object']}",
                        "semantic": m["semantic_score"],
                        "graph": m["graph_score"],
                        "final": m["final_score"],
                    }
                    for m in retrieved
                ]
            },
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    )

    memory_context = context_text(retrieved)
    started = time.perf_counter()
    answer = response_agent(query, memory_context, history, scenario_name)
    stages.append(
        AgentStage(
            name="Response Composer",
            summary="Generated a scenario-grounded response from retrieved evidence",
            details={"context_memories": len(retrieved), "scenario": scenario_name},
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    )

    user_message = Message(workspace_id=workspace_id, role="user", content=query)
    assistant_message = Message(workspace_id=workspace_id, role="assistant", content=answer)
    store.add_message(user_message)
    store.add_message(assistant_message)

    started = time.perf_counter()
    raw_candidates = extract_agent(query, history, scenario_name, retrieved)
    stages.append(
        AgentStage(
            name="Memory Extraction Agent",
            summary=f"Extracted {len(raw_candidates)} durable candidate memories",
            details={"candidates": [candidate.model_dump() for candidate in raw_candidates]},
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    )

    started = time.perf_counter()
    resolved_candidates, resolution_notes = resolve_candidates(raw_candidates, existing_memories)
    stages.append(
        AgentStage(
            name="Entity Resolution Agent",
            summary=f"Normalized {len(resolved_candidates)} candidate memories",
            details={"resolutions": resolution_notes},
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    )

    started = time.perf_counter()
    comparisons: list[tuple[MemoryCandidate, ConflictDecision, dict | None]] = []
    for candidate in resolved_candidates:
        decision, existing = conflict_agent(candidate, existing_memories)
        comparisons.append((candidate, decision, existing))
    stages.append(
        AgentStage(
            name="Conflict & Consolidation Agent",
            summary=f"Classified {len(comparisons)} memory relationships",
            details={
                "comparisons": [
                    {
                        "candidate": candidate.model_dump(),
                        "decision": decision.model_dump(),
                        "existing_memory_id": existing.get("id") if existing else None,
                    }
                    for candidate, decision, existing in comparisons
                ]
            },
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    )

    started = time.perf_counter()
    decisions: list[dict] = []
    added_ids: list[str] = []
    updated_ids: list[str] = []
    pending_ids: list[str] = []
    ignored_count = 0

    for candidate, decision, existing in comparisons:
        proposal_id = f"proposal_{uuid4().hex[:10]}"
        persistence = "observed"
        memory_id: str | None = None

        if memory_mode == "Automatic":
            safe_to_write = (
                candidate.confidence >= settings.auto_memory_threshold
                and decision.relationship not in {"contradiction", "supersedes"}
            ) or decision.relationship == "duplicate"
            if safe_to_write:
                memory_id, persistence = _persist_candidate(
                    store,
                    workspace_id,
                    candidate,
                    decision,
                    existing,
                    user_message.id,
                )
                (updated_ids if persistence == "updated" else added_ids).append(memory_id)
            else:
                persistence = "pending"
                pending_ids.append(proposal_id)
        elif memory_mode == "Review":
            persistence = "pending"
            pending_ids.append(proposal_id)
        else:
            persistence = "observed"
            ignored_count += 1

        decisions.append(
            {
                "proposal_id": proposal_id,
                "candidate": candidate.model_dump(),
                "decision": decision.model_dump(),
                "existing_memory_id": existing.get("id") if existing else None,
                "memory_id": memory_id,
                "persistence": persistence,
                "source_message_id": user_message.id,
            }
        )

    stages.append(
        AgentStage(
            name="Memory Writer",
            summary=(
                f"{len(added_ids)} added · {len(updated_ids)} updated · "
                f"{len(pending_ids)} pending · {ignored_count} observed only"
            ),
            details={"mode": memory_mode, "decisions": decisions},
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    )

    after_memories = store.list_memories(workspace_id)
    graph_delta = GraphDelta(
        added_ids=added_ids,
        updated_ids=updated_ids,
        pending_ids=pending_ids,
        ignored_count=ignored_count,
        before_memories=before_memory_count,
        after_memories=len(after_memories),
        before_entities=before_entity_count,
        after_entities=entity_count(after_memories),
    )

    trace = AgentTrace(
        workspace_id=workspace_id,
        query=query,
        memory_mode=memory_mode,
        stages=stages,
        retrieved_memories=retrieved,
        new_memory_decisions=decisions,
        graph_delta=graph_delta,
        final_context=memory_context,
    )
    store.add_trace(trace)
    return answer, trace
