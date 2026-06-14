from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

MemoryType = Literal[
    "preference",
    "goal",
    "skill",
    "project",
    "constraint",
    "fact",
    "event",
]
MemoryStatus = Literal[
    "candidate",
    "active",
    "confirmed",
    "superseded",
    "contradicted",
    "archived",
]
MemoryMode = Literal["Automatic", "Review", "Observe only"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryCandidate(BaseModel):
    memory_type: MemoryType = "fact"
    subject: str
    relation: str
    object: str
    confidence: float = Field(default=0.8, ge=0, le=1)
    importance: float = Field(default=0.7, ge=0, le=1)
    evidence: str = ""


class MemoryItem(MemoryCandidate):
    id: str = Field(default_factory=lambda: f"mem_{uuid4().hex[:12]}")
    workspace_id: str
    status: MemoryStatus = "active"
    mention_count: int = 1
    first_seen_at: str = Field(default_factory=now_iso)
    last_seen_at: str = Field(default_factory=now_iso)
    source_message_id: str | None = None
    embedding: list[float] | None = None


class Message(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:12]}")
    workspace_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str = Field(default_factory=now_iso)


class ConflictDecision(BaseModel):
    relationship: Literal[
        "new",
        "duplicate",
        "refinement",
        "complement",
        "contradiction",
        "supersedes",
    ]
    explanation: str
    action: str
    confidence: float = Field(default=0.8, ge=0, le=1)


class IntentPlan(BaseModel):
    intent: str = "general_assistance"
    needed_memory_types: list[str] = Field(default_factory=list)
    retrieval_mode: Literal["vector", "graph", "hybrid"] = "hybrid"
    query_entities: list[str] = Field(default_factory=list)


class AgentStage(BaseModel):
    name: str
    status: Literal["completed", "skipped", "fallback", "failed"] = "completed"
    summary: str
    details: dict = Field(default_factory=dict)
    duration_ms: int = 0


class GraphDelta(BaseModel):
    added_ids: list[str] = Field(default_factory=list)
    updated_ids: list[str] = Field(default_factory=list)
    pending_ids: list[str] = Field(default_factory=list)
    ignored_count: int = 0
    before_memories: int = 0
    after_memories: int = 0
    before_entities: int = 0
    after_entities: int = 0


class AgentTrace(BaseModel):
    id: str = Field(default_factory=lambda: f"trace_{uuid4().hex[:12]}")
    workspace_id: str
    query: str
    memory_mode: MemoryMode = "Automatic"
    stages: list[AgentStage]
    retrieved_memories: list[dict] = Field(default_factory=list)
    new_memory_decisions: list[dict] = Field(default_factory=list)
    graph_delta: GraphDelta = Field(default_factory=GraphDelta)
    final_context: str = ""
    created_at: str = Field(default_factory=now_iso)
