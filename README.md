# GraphMind Studio

**Visual Hybrid Memory for LLMs Through Agent Orchestration**

GraphMind Studio is an interactive Streamlit workbench that converts evolving conversations with LLMs into evidence-linked episodic and semantic memory using knowledge graphs and vector memory. Instead of storing only recent chat turns, summaries, or vector chunks, the framework represents durable information as typed, evidence-linked relationships and makes the complete memory read/write workflow inspectable.

A visitor starts from a seeded fictional scenario, continues the conversation, and watches the graph evolve. Each turn shows which memories grounded the answer, what new information was extracted, how entities were normalized, whether a candidate duplicated or conflicted with existing memory, and what was ultimately written to the graph.

The application is designed to be:

- safe for public demonstration without exposing real personal history;
- runnable locally in VS Code without Docker or Neo4j;
- deployable on Streamlit Community Cloud;
- usable with a local JSON store during development;
- compatible with Supabase/PostgreSQL for durable cloud persistence;
- understandable through visual orchestration, graph, evidence, and lifecycle views.

---

## 1. Why GraphMind?

Simple LLM memory usually relies on:

- recent messages placed back into the context window;
- compressed conversation summaries;
- vector embeddings of conversation chunks.

Those mechanisms are useful for semantic recall, but they are weak at representing explicit relationships and changes such as:

```text
Dr. Lena Hoffmann → COMPLETED_MASTERS_AT → Technical University of Munich
Dr. Lena Hoffmann → ENJOYS → Hiking
ReasonScope → CONTAINS → Bias Comparison Engine
Orchestrix → USES_EVALUATION_FROM → ReasonScope
New preference → REFINES → Earlier preference
```

GraphMind combines semantic-style retrieval with graph-neighborhood relevance, typed memories, temporal metadata, conflict analysis, and user-controlled memory writing.

The framework demonstrates:

- symbolic consistency;
- relationship and entity tracking;
- changing preferences and constraints;
- cross-turn and cross-session memory;
- duplicate, refinement, and contradiction handling;
- explicit evidence and confidence;
- observable multi-agent orchestration.

---

## 2. Scenario design

The app includes three seeded fictional scenarios. The **Overview page remains scenario-independent** and explains the framework itself. A compact dynamic scenario card appears in **Memory Lab** and **Graph Explorer**, so every scenario is introduced consistently where its context is actually needed.

### AI Researcher

**Dr. Lena Hoffmann** is a clearly labeled synthetic persona. Her memory is intentionally balanced across education, research, hobbies, everyday preferences, and two imaginary research systems.

Educational background:

- bachelor's degree in Computer Science at the University of Stuttgart;
- master's degree in Artificial Intelligence at the Technical University of Munich;
- doctorate at the Technical University of Munich.

Research profile:

- LLM reasoning reliability;
- reasoning bias;
- parameter-efficient fine-tuning;
- multi-agent orchestration;
- modular system design;
- reproducible evaluation.

Everyday context:

- hiking;
- classical music;
- science-fiction reading;
- quiet cafés;
- living in Munich;
- learning Italian.

The scenario contains only two imaginary projects:

#### ReasonScope

A fictional reasoning and bias evaluation system connected to explicit components:

- Controlled Prompt Generator;
- Reasoning Consistency Analyzer;
- Bias Comparison Engine;
- Evaluation Dashboard.

#### Orchestrix

A fictional multi-agent system-design platform connected to:

- Orchestration Controller;
- Planning Agent;
- Retrieval Agent;
- Hybrid Memory Layer;
- Evaluation Agent;
- Trace Monitor.

The projects form a small connected ecosystem:

```text
Orchestrix → PROVIDES_TRACES_TO → ReasonScope
ReasonScope → EVALUATES → Orchestrix
Orchestrix → USES_EVALUATION_FROM → ReasonScope
```

Fine-tuning remains part of the researcher's expertise rather than becoming a third project. This keeps the graph realistic and readable.

### Product Manager

A fictional product workspace tracking:

- customer priorities;
- roadmap decisions;
- stakeholder needs;
- delivery constraints;
- evolving requirements.

### Travel Planner

A fictional travel workspace tracking:

- destination and transport preferences;
- companions;
- budget and pace;
- changing plans and constraints.

---

## 3. Core capabilities

### Dynamic scenario conversations

A scenario is the starting memory state, not a static graph. Visitors can continue with ordinary or domain-specific conversation. For example, the AI Researcher suggestions intentionally include simple messages:

```text
I want Orchestrix to keep evaluation independent from response generation.
I enjoy amateur astronomy and photographing the night sky during weekend hikes.
I have recently started learning Italian through films and music.
```

These turns demonstrate that long-term memory should represent a person or role as a multidimensional entity rather than only as a list of technical projects.

### Isolated visitor workspaces

Every Streamlit session receives a unique cloned workspace. Therefore:

- the shared seed remains unchanged;
- visitors do not overwrite one another's graph;
- reset affects only the active visitor workspace;
- a fresh isolated copy can be created from the sidebar.

### Hybrid memory retrieval

Before answering, the Retrieval Agent combines:

- semantic-style lexical similarity in local mode;
- direct entity relevance;
- graph-neighborhood relevance;
- memory-type relevance;
- confidence and importance;
- confirmation frequency.

The Evaluation page compares:

- vector-only ranking;
- graph-only ranking;
- hybrid ranking.

The local lexical signal keeps the project lightweight. The Supabase schema includes a pgvector column and `match_memories` function for an embedding-backed extension.

### Cross-turn memory extraction

The Memory Extraction Agent receives:

- the current user message;
- a configurable recent conversation window;
- the active scenario definition;
- related memories retrieved for the answer.

This supports reference resolution and avoids storing isolated phrases without conversational meaning.

### Entity resolution

Candidate entities are normalized before storage. Examples include:

```text
KG → Knowledge Graph
RAG → Retrieval-Augmented Generation
Streamlit Cloud → Streamlit Community Cloud
```

Known graph entities are reused when normalized names match.

### Conflict and consolidation analysis

Each candidate is classified as:

- `new`;
- `duplicate`;
- `refinement`;
- `complement`;
- `contradiction`;
- `supersedes`.

Duplicates confirm existing memories. Contradictions and superseding candidates can be held for review rather than silently rewriting memory.

### Memory governance

GraphMind supports three policies.

#### Automatic

High-confidence, non-conflicting memories are written immediately. Ambiguous or conflicting candidates remain pending.

#### Review

Every candidate appears in an editable form. The visitor can revise the memory type, subject, relation, object, confidence, importance, and evidence before approval.

#### Observe only

The complete pipeline runs, but nothing is persisted. This is useful for safe demonstrations and evaluation.

### Graph-delta visualization

Every turn records:

- new relationships;
- confirmed or updated relationships;
- pending review proposals;
- ignored candidates;
- entity-count changes.

The Graph Explorer highlights newly written, updated, contradicted, pending, and answer-grounding relationships.

---

## 4. Agent orchestration

Each conversation turn follows an explicit read and write path:

```text
User request
   ↓
Intent Agent
   ↓
Hybrid Retrieval Agent
   ↓
Context Builder
   ↓
Response Composer
   ↓
Memory Extraction Agent
   ↓
Entity Resolution Agent
   ↓
Conflict and Consolidation Agent
   ↓
Memory Writer
   ↓
Graph Delta
```

The Agent Trace page displays structured inputs, decisions, evidence, status, and latency. It does not expose private hidden chain-of-thought.

---

## 5. Interface

### Overview

Scenario-independent explanation of:

- hybrid recall;
- dynamic graph memory;
- conflict-aware updates;
- observable orchestration;
- read, write, and control paths;
- overall system metrics.

The selected persona is deliberately not expanded on this page, keeping the landing experience concise.

### Memory Lab

Includes:

- a compact dynamic scenario card;
- scenario-appropriate suggested chats;
- conversation history;
- memories used for the answer;
- memory policy explanation;
- agent orchestration;
- graph-delta summary;
- editable review proposals.

### Graph Explorer

Includes the same compact scenario context and three progressively broader views:

- **Recent updates** isolates relationships added or confirmed by the latest conversation turn and is the default view;
- **Focused graph** shows a readable one-hop neighborhood around any selected person, project, component, preference, or concept, with optional second-hop context;
- **Full graph** remains available for advanced inspection.

Advanced type, status, and entity filters are placed inside a collapsed panel. The Evidence Inspector sorts relationships by `last_seen_at` and then `first_seen_at`, so the newest or most recently confirmed relationship appears first.

### Agent Trace

Shows structured agent outputs, final memory context, write decisions, and graph changes.

### Evaluation

Compares vector-only, graph-only, and hybrid retrieval scores for the same query.

### Memory Manager

Allows stored memories to be confirmed, archived, marked contradicted, and inspected with their evidence and metadata.

---

## 6. Project structure

```text
graphmind_studio/
├── app.py
├── graphmind/
│   ├── config.py
│   ├── llm.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── scenarios.py
│   ├── storage.py
│   └── ui.py
├── supabase/
│   └── schema.sql
├── tests/
│   └── test_core.py
├── .streamlit/
│   ├── config.toml
│   └── secrets.example.toml
├── .env.example
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

---

## 7. Local setup in VS Code

Use Python 3.12.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-5.4-mini
EMBEDDING_MODEL=text-embedding-3-small

BACKEND_MODE=local
SUPABASE_URL=
SUPABASE_KEY=

AUTO_MEMORY_THRESHOLD=0.80
CONVERSATION_CONTEXT_TURNS=6
```

Run:

```powershell
python -m streamlit run app.py
```

The app can open without an OpenAI key. In that case it uses deterministic fallbacks for basic responses and common memory patterns.

---

## 8. Supabase setup

Supabase is optional locally and recommended for durable cloud persistence.

1. Create a Supabase project.
2. Open the SQL Editor.
3. Run `supabase/schema.sql`.
4. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` for local testing, or add the values through Streamlit Cloud settings.
5. Set `BACKEND_MODE` to `supabase`.

Example:

```toml
OPENAI_API_KEY = "your-openai-key"
OPENAI_MODEL = "gpt-5.4-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
BACKEND_MODE = "supabase"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-server-side-key"
AUTO_MEMORY_THRESHOLD = "0.80"
CONVERSATION_CONTEXT_TURNS = "6"
```

Do not commit `.env` or `.streamlit/secrets.toml`.

### Security note

The supplied schema is suitable for a controlled technical demo using a server-side key stored in Streamlit secrets. Before storing sensitive data or adding public accounts, implement Supabase Auth, row-level-security policies, user-owned workspaces, retention controls, and deletion workflows.

---

## 9. Streamlit Community Cloud

Recommended deployment configuration:

- entry point: `app.py`;
- Python: 3.12;
- secrets added through App settings;
- Supabase for durable persistence.

No Docker, Neo4j server, ChromaDB service, or local database server is required.

Local JSON mode is useful for development but should not be considered durable cloud storage because the Streamlit environment can restart.

---

## 10. Suggested demonstration

### Balanced dynamic-memory demonstration

1. Select **AI Researcher**.
2. Keep **Automatic** mode.
3. Enter:

```text
I want Orchestrix to keep evaluation independent from response generation.
```

4. Inspect the project-level graph update and agent trace.
5. Enter a science-related hobby:

```text
I enjoy amateur astronomy and photographing the night sky during weekend hikes.
```

6. Enter a non-technical hobby or learning preference:

```text
I have recently started learning Italian through films and music.
```

7. Open Graph Explorer. Recent updates isolates the newest link, while Focused graph lets you inspect its local neighborhood without loading the full graph.

### Review-mode demonstration

Switch to **Review** mode and repeat one of the statements. Edit the proposed subject, relation, or object before approval. This demonstrates user control over an evolving memory graph.

### Observe-only demonstration

1. Switch to **Observe only**.
2. Add a potentially conflicting preference.
3. Inspect the complete orchestration trace.
4. Verify that the graph counts do not change.

---

## 11. Memory data model

A stored memory resembles:

```json
{
  "id": "mem_123",
  "workspace_id": "ai_researcher_v4_visitor",
  "memory_type": "preference",
  "subject": "Dr. Lena Hoffmann",
  "relation": "PREFERS",
  "object": "Amateur astronomy",
  "evidence": "I enjoy amateur astronomy and photographing the night sky during weekend hikes.",
  "confidence": 0.91,
  "importance": 0.72,
  "status": "active",
  "mention_count": 1,
  "first_seen_at": "...",
  "last_seen_at": "..."
}
```

Lifecycle states include:

- candidate;
- active;
- confirmed;
- superseded;
- contradicted;
- archived.

---

## 12. Retrieval scoring

The local hybrid policy uses an inspectable weighted combination of:

```text
semantic similarity
+ graph proximity
+ memory-type relevance
+ importance
+ confidence
+ confirmation frequency
```

This is an MVP policy, not a theoretically optimal ranking model. A rigorous extension should evaluate labeled queries using Precision@k, Recall@k, MRR, relationship coverage, conflict-aware accuracy, and memory citation coverage.

---

## 13. Tests

Run:

```powershell
python -m unittest discover -s tests -v
```

The test suite covers:

- isolated scenario cloning;
- automatic memory writing;
- observe-only non-persistence;
- review approval;
- duplicate confirmation;
- two-project component connectivity;
- educational and hobby memories;
- vector, graph, and hybrid retrieval.

---

## 14. Recommended future improvements

### Real pgvector retrieval

Write embeddings for each memory and query Supabase through `match_memories`, then combine those results with graph-neighborhood traversal.

### Visitor identity and row-level security

Add Supabase Auth and user-owned workspaces for a true multi-user deployment.

### Temporal visualization

Add a dedicated timeline for first observation, confirmation, refinement, contradiction, supersession, and archival.

### Evaluation benchmark

Create labeled query sets covering direct recall, multi-hop retrieval, preference changes, contradiction resolution, entity aliases, and irrelevant-memory rejection.

### Cost and token telemetry

Record model, latency, token usage, and estimated cost for each agent stage.

### Downloadable experiment reports

Export the query, retrieved memories, graph paths, conflict decisions, graph delta, and final response as JSON or CSV.

---

## 15. Project summary

> GraphMind Studio is a cloud-deployable hybrid memory and orchestration framework that converts evolving conversations into evidence-linked knowledge graphs, combines semantic and relationship-aware retrieval, detects duplicate and conflicting memories, and visualizes agent decisions and graph updates in Streamlit.

Technical highlights:

- Multi-agent pipeline for intent planning, hybrid retrieval, response composition, extraction, entity resolution, conflict detection, and controlled graph updates.
- Automatic, review, and observe-only memory policies.
- Isolated role-based workspaces suitable for public demonstrations.
- Balanced fictional AI Researcher data covering education, hobbies, preferences, research interests, and two connected imaginary projects.
- Interactive graph, component, ecosystem, evidence, trace, lifecycle, and retrieval-comparison views.
- Pluggable local JSON and Supabase/PostgreSQL storage.

---

## 16. Intended use

GraphMind Studio is intended for education, experimentation, and technical demonstration. It should not be used as-is to store sensitive personal data or support high-stakes decisions. Add an appropriate repository license before public release.
