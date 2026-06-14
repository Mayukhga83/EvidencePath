# Changelog

## Contextual memory-update placement

- Moved the latest memory update directly below the newest assistant response in Memory Lab.
- Added a compact highlighted card for added, updated, pending, observed, and rejected memory decisions.
- Added a nearby View graph change action when the latest turn changed the graph.
- Moved the full decision explanation into a collapsed panel beside the live memory context.
- Removed the duplicate long decision cards and duplicate graph button from the bottom of Memory Lab.

## Simplified graph inspection and balanced prompts

- Replaced four project-specific graph modes with Recent updates, Focused graph, and Full graph.
- Made Recent updates the default and isolated relationships changed by the latest conversation turn.
- Added a generic one-hop entity neighborhood with optional second-hop context.
- Moved memory-type, status, and search controls into a collapsed Advanced filters panel.
- Sorted Evidence Inspector relationships newest-first using `last_seen_at` and `first_seen_at`.
- Automatically selects the newest relationship after a graph update.
- Balanced AI Researcher suggested conversations across one project decision, one science-related hobby, and one other hobby.
- Updated the Overview headline, hero description, and framework heading.
- Bumped the AI Researcher scenario seed to v4.

## Balanced scenario and simplified overview

- Reduced the fictional AI Researcher workspace from three projects to two: ReasonScope and Orchestrix.
- Added bachelor's, master's, and doctoral education relationships.
- Added hobbies and everyday preferences including hiking, music, reading, cafés, location, and language learning.
- Replaced technical-only suggested chats with simple everyday conversation examples.
- Removed persona and project demonstration cards from the Overview page.
- Added a compact dynamic scenario card to Memory Lab and Graph Explorer for every scenario.
- Updated deterministic extraction to recognize `I enjoy` and `I love` preference statements.
- Removed the old CV-oriented fallback response.
- Updated tests and documentation.

## 2.1.0 — Synthetic research ecosystem

- Replaced the AI Researcher profile with the explicitly fictional Dr. Lena Hoffmann persona.
- Removed CV, job-application, and real-project references from the scenario data and examples.
- Reduced the fictional research portfolio to three connected systems: ReasonScope, AdaptLab, and Orchestrix.
- Added explicit functional-component nodes and cross-project model/evaluation dependencies.
- Added Project overview, Project components, Research ecosystem, and Full graph views.
- Added node-role styling for persona, project, component, and concept/output nodes.
- Normalized first-person memory extraction to the scenario persona.
- Versioned the AI Researcher seed to prevent old local scenario data from being reused accidentally.
- Expanded automated tests for component and cross-project graph structure.

## Dynamic Memory Update Edition

- Added isolated cloned workspaces for every Streamlit visitor session.
- Added role-grounded continued conversations for all preset scenarios.
- Added Automatic, Review, and Observe-only memory policies.
- Added cross-turn memory extraction using recent conversation context.
- Added entity normalization and alias resolution.
- Added explicit duplicate, refinement, complement, contradiction, and superseding classifications.
- Added editable memory-proposal approval forms.
- Added graph-delta tracking and visual highlighting of added, updated, and answer-grounding relationships.
- Expanded the Overview page to explain read, write, and governance paths.
- Expanded the Agent Trace and Evaluation views.
- Updated the Supabase schema for isolated workspaces.
- Added local core tests and a comprehensive deployment README.
