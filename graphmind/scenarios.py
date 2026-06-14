from __future__ import annotations

SCENARIOS = {
    "AI Researcher": {
        "workspace": {
            "id": "demo_ai_researcher",
            "name": "AI Researcher",
            "description": (
                "A fictional AI researcher whose memory spans education, research interests, "
                "everyday preferences, hobbies, and two imaginary research systems."
            ),
            "scenario": "AI Researcher",
        },
        "display_title": "AI Researcher · Dr. Lena Hoffmann",
        "scenario_tags": ["Education and hobbies", "Research interests", "2 imaginary projects"],
        "persona_name": "Dr. Lena Hoffmann",
        "fictional_persona": True,
        "seed_version": "v4",
        "projects": ["ReasonScope", "Orchestrix"],
        "project_components": {
            "ReasonScope": [
                "Controlled Prompt Generator",
                "Reasoning Consistency Analyzer",
                "Bias Comparison Engine",
                "Evaluation Dashboard",
            ],
            "Orchestrix": [
                "Orchestration Controller",
                "Planning Agent",
                "Retrieval Agent",
                "Hybrid Memory Layer",
                "Evaluation Agent",
                "Trace Monitor",
            ],
        },
        "project_purpose_relations": ["INVESTIGATES", "DESIGNS"],
        "ecosystem_relations": [
            "WORKED_ON",
            "INVESTIGATES",
            "DESIGNS",
            "EVALUATES",
            "PROVIDES_TRACES_TO",
            "USES_EVALUATION_FROM",
        ],
        "role_prompt": (
            "Act as a memory-aware assistant for the fictional researcher Dr. Lena Hoffmann. "
            "Support both ordinary conversation and research collaboration. Use education, hobbies, "
            "preferences, and research context only when relevant. Do not force technical topics into "
            "simple everyday exchanges. For research questions, prioritize rigorous evaluation, modular "
            "system design, reasoning reliability, and transparent trade-offs."
        ),
        "memory_priorities": ["preference", "fact", "event", "goal", "skill", "project", "constraint"],
        "demo_prompts": [
            "I want Orchestrix to keep evaluation independent from response generation.",
            "I enjoy amateur astronomy and photographing the night sky during weekend hikes.",
            "I have recently started learning Italian through films and music.",
        ],
        "memories": [
            # Educational background
            {"memory_type": "fact", "subject": "Dr. Lena Hoffmann", "relation": "COMPLETED_BACHELORS_AT", "object": "University of Stuttgart", "confidence": 0.99, "importance": 0.86, "evidence": "The fictional researcher completed a bachelor's degree in Computer Science at the University of Stuttgart."},
            {"memory_type": "fact", "subject": "Bachelor's degree", "relation": "FIELD_OF_STUDY", "object": "Computer Science", "confidence": 0.99, "importance": 0.79, "evidence": "Her bachelor's programme focused on Computer Science."},
            {"memory_type": "fact", "subject": "Dr. Lena Hoffmann", "relation": "COMPLETED_MASTERS_AT", "object": "Technical University of Munich", "confidence": 0.99, "importance": 0.89, "evidence": "She completed a master's degree in Artificial Intelligence at the Technical University of Munich."},
            {"memory_type": "fact", "subject": "Master's degree", "relation": "FIELD_OF_STUDY", "object": "Artificial Intelligence", "confidence": 0.99, "importance": 0.84, "evidence": "Her master's programme focused on Artificial Intelligence."},
            {"memory_type": "fact", "subject": "Dr. Lena Hoffmann", "relation": "COMPLETED_PHD_AT", "object": "Technical University of Munich", "confidence": 0.99, "importance": 0.90, "evidence": "The fictional researcher later completed a doctorate at the Technical University of Munich."},

            # Research profile
            {"memory_type": "fact", "subject": "Dr. Lena Hoffmann", "relation": "RESEARCHES", "object": "LLM reasoning reliability", "confidence": 0.98, "importance": 0.96, "evidence": "Her research examines how reliably language models perform structured reasoning."},
            {"memory_type": "fact", "subject": "Dr. Lena Hoffmann", "relation": "RESEARCHES", "object": "Reasoning bias", "confidence": 0.97, "importance": 0.94, "evidence": "She studies how controlled variations can alter model conclusions and explanations."},
            {"memory_type": "skill", "subject": "Dr. Lena Hoffmann", "relation": "HAS_EXPERIENCE_WITH", "object": "Parameter-efficient fine-tuning", "confidence": 0.96, "importance": 0.88, "evidence": "Her experimental background includes LoRA- and QLoRA-based adaptation."},
            {"memory_type": "skill", "subject": "Dr. Lena Hoffmann", "relation": "HAS_EXPERIENCE_WITH", "object": "Multi-agent orchestration", "confidence": 0.95, "importance": 0.89, "evidence": "She designs systems coordinating planning, retrieval, evaluation, and response stages."},
            {"memory_type": "preference", "subject": "Dr. Lena Hoffmann", "relation": "PREFERS", "object": "Modular system architectures", "confidence": 0.94, "importance": 0.83, "evidence": "She prefers independently testable components with explicit interfaces."},
            {"memory_type": "preference", "subject": "Dr. Lena Hoffmann", "relation": "VALUES", "object": "Reproducible evaluation", "confidence": 0.97, "importance": 0.91, "evidence": "She values repeatable experiments and evidence-linked conclusions."},

            # Hobbies and everyday preferences
            {"memory_type": "preference", "subject": "Dr. Lena Hoffmann", "relation": "ENJOYS", "object": "Hiking", "confidence": 0.95, "importance": 0.68, "evidence": "She often goes hiking on weekends."},
            {"memory_type": "preference", "subject": "Dr. Lena Hoffmann", "relation": "LISTENS_TO", "object": "Classical music", "confidence": 0.91, "importance": 0.61, "evidence": "She enjoys listening to classical music while reading."},
            {"memory_type": "preference", "subject": "Dr. Lena Hoffmann", "relation": "READS", "object": "Science-fiction novels", "confidence": 0.92, "importance": 0.66, "evidence": "Science-fiction novels are part of her regular leisure reading."},
            {"memory_type": "preference", "subject": "Dr. Lena Hoffmann", "relation": "PREFERS", "object": "Quiet cafés", "confidence": 0.90, "importance": 0.62, "evidence": "She prefers quiet cafés when reading or writing notes."},
            {"memory_type": "fact", "subject": "Dr. Lena Hoffmann", "relation": "LIVES_IN", "object": "Munich", "confidence": 0.94, "importance": 0.58, "evidence": "The fictional persona currently lives in Munich."},
            {"memory_type": "goal", "subject": "Dr. Lena Hoffmann", "relation": "IS_LEARNING", "object": "Italian", "confidence": 0.89, "importance": 0.57, "evidence": "She is casually learning Italian outside work."},

            # Project 1: ReasonScope and functional components
            {"memory_type": "project", "subject": "Dr. Lena Hoffmann", "relation": "WORKED_ON", "object": "ReasonScope", "confidence": 0.99, "importance": 0.91, "evidence": "ReasonScope is a fictional research system for reasoning and bias evaluation."},
            {"memory_type": "fact", "subject": "ReasonScope", "relation": "INVESTIGATES", "object": "LLM reasoning reliability", "confidence": 0.99, "importance": 0.94, "evidence": "ReasonScope compares reasoning behaviour across prompts, models, and controlled variations."},
            {"memory_type": "fact", "subject": "ReasonScope", "relation": "CONTAINS", "object": "Controlled Prompt Generator", "confidence": 0.99, "importance": 0.85, "evidence": "The generator creates matched reasoning tasks and controlled prompt variations."},
            {"memory_type": "fact", "subject": "ReasonScope", "relation": "CONTAINS", "object": "Reasoning Consistency Analyzer", "confidence": 0.99, "importance": 0.88, "evidence": "The analyzer compares answer and rationale consistency across repeated conditions."},
            {"memory_type": "fact", "subject": "ReasonScope", "relation": "CONTAINS", "object": "Bias Comparison Engine", "confidence": 0.99, "importance": 0.89, "evidence": "The engine compares reasoning shifts across controlled contextual variations."},
            {"memory_type": "fact", "subject": "ReasonScope", "relation": "CONTAINS", "object": "Evaluation Dashboard", "confidence": 0.99, "importance": 0.80, "evidence": "The dashboard presents reasoning consistency, bias, and failure-pattern metrics."},
            {"memory_type": "fact", "subject": "Controlled Prompt Generator", "relation": "CREATES", "object": "Matched reasoning tasks", "confidence": 0.98, "importance": 0.82, "evidence": "It creates comparable variants while holding the underlying task stable."},
            {"memory_type": "fact", "subject": "Reasoning Consistency Analyzer", "relation": "MEASURES", "object": "Cross-prompt consistency", "confidence": 0.98, "importance": 0.87, "evidence": "It measures whether conclusions remain stable across equivalent prompt formulations."},
            {"memory_type": "fact", "subject": "Bias Comparison Engine", "relation": "DETECTS", "object": "Reasoning shifts", "confidence": 0.98, "importance": 0.90, "evidence": "It detects changes in conclusions or explanations under controlled variations."},
            {"memory_type": "fact", "subject": "Evaluation Dashboard", "relation": "VISUALIZES", "object": "Consistency and bias metrics", "confidence": 0.97, "importance": 0.78, "evidence": "It visualizes aggregate consistency, subgroup shifts, and representative failures."},

            # Project 2: Orchestrix and functional components
            {"memory_type": "project", "subject": "Dr. Lena Hoffmann", "relation": "WORKED_ON", "object": "Orchestrix", "confidence": 0.99, "importance": 0.93, "evidence": "Orchestrix is a fictional multi-agent systems research platform."},
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "DESIGNS", "object": "Multi-agent LLM systems", "confidence": 0.99, "importance": 0.94, "evidence": "Orchestrix studies modular coordination across specialized LLM agents."},
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "CONTAINS", "object": "Orchestration Controller", "confidence": 0.99, "importance": 0.91, "evidence": "The controller routes tasks and maintains explicit stage boundaries."},
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "CONTAINS", "object": "Planning Agent", "confidence": 0.99, "importance": 0.85, "evidence": "The Planning Agent converts requests into structured execution plans."},
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "CONTAINS", "object": "Retrieval Agent", "confidence": 0.99, "importance": 0.87, "evidence": "The Retrieval Agent selects evidence and prior memory for downstream stages."},
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "CONTAINS", "object": "Hybrid Memory Layer", "confidence": 0.99, "importance": 0.92, "evidence": "The memory layer combines semantic retrieval with explicit relationship memory."},
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "CONTAINS", "object": "Evaluation Agent", "confidence": 0.99, "importance": 0.90, "evidence": "The Evaluation Agent independently checks candidate outputs and supporting evidence."},
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "CONTAINS", "object": "Trace Monitor", "confidence": 0.99, "importance": 0.83, "evidence": "The Trace Monitor records structured stage decisions, latency, and outcomes."},
            {"memory_type": "fact", "subject": "Orchestration Controller", "relation": "ROUTES_TASKS_TO", "object": "Specialized agents", "confidence": 0.99, "importance": 0.87, "evidence": "It routes work according to explicit responsibilities and stage outputs."},
            {"memory_type": "fact", "subject": "Planning Agent", "relation": "CREATES", "object": "Execution plans", "confidence": 0.98, "importance": 0.82, "evidence": "The Planning Agent creates inspectable execution steps for complex requests."},
            {"memory_type": "fact", "subject": "Retrieval Agent", "relation": "FETCHES", "object": "Relevant evidence", "confidence": 0.99, "importance": 0.86, "evidence": "It retrieves evidence from semantic and structured memory sources."},
            {"memory_type": "fact", "subject": "Hybrid Memory Layer", "relation": "COMBINES", "object": "Semantic retrieval", "confidence": 0.99, "importance": 0.88, "evidence": "Semantic retrieval supports similarity-based recall."},
            {"memory_type": "fact", "subject": "Hybrid Memory Layer", "relation": "COMBINES", "object": "Graph memory", "confidence": 0.99, "importance": 0.90, "evidence": "Graph memory preserves explicit entities, relations, and changes."},
            {"memory_type": "fact", "subject": "Evaluation Agent", "relation": "VALIDATES", "object": "Candidate responses", "confidence": 0.99, "importance": 0.88, "evidence": "It validates candidate responses independently from response generation."},
            {"memory_type": "fact", "subject": "Trace Monitor", "relation": "RECORDS", "object": "Agent decisions", "confidence": 0.98, "importance": 0.83, "evidence": "It records structured decisions without exposing hidden chain-of-thought."},

            # Cross-project ecosystem
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "PROVIDES_TRACES_TO", "object": "ReasonScope", "confidence": 0.98, "importance": 0.89, "evidence": "Orchestrix provides structured agent traces for reliability analysis in ReasonScope."},
            {"memory_type": "fact", "subject": "ReasonScope", "relation": "EVALUATES", "object": "Orchestrix", "confidence": 0.98, "importance": 0.91, "evidence": "ReasonScope evaluates the consistency and bias of Orchestrix agent behaviour."},
            {"memory_type": "fact", "subject": "Orchestrix", "relation": "USES_EVALUATION_FROM", "object": "ReasonScope", "confidence": 0.98, "importance": 0.90, "evidence": "Orchestrix uses ReasonScope findings to improve agent reliability."},
        ],
    },
    "Product Manager": {
        "workspace": {
            "id": "demo_product_manager",
            "name": "Product Manager",
            "description": "A fictional product workspace tracking customer priorities, roadmap decisions, stakeholder needs, and delivery constraints.",
            "scenario": "Product Manager",
        },
        "display_title": "Product Manager Workspace",
        "scenario_tags": ["Customer priorities", "Roadmap decisions", "Delivery constraints"],
        "seed_version": "v2",
        "role_prompt": (
            "Act as a product strategy assistant. Prioritize customer evidence, stakeholder relationships, "
            "delivery risk, requirements, roadmap trade-offs, and measurable outcomes."
        ),
        "memory_priorities": ["goal", "constraint", "fact", "project", "preference", "event"],
        "demo_prompts": [
            "What should the team prioritize in the next sprint?",
            "The deadline is now flexible, but security approval is mandatory.",
            "Customers are asking for self-service permission templates.",
        ],
        "memories": [
            {"memory_type": "goal", "subject": "User", "relation": "HAS_GOAL", "object": "Reduce enterprise onboarding time", "confidence": 0.96, "importance": 0.96, "evidence": "Our primary objective is faster onboarding."},
            {"memory_type": "preference", "subject": "User", "relation": "PREFERS", "object": "Evidence-backed roadmap decisions", "confidence": 0.92, "importance": 0.87, "evidence": "Roadmap decisions must reference customer evidence."},
            {"memory_type": "constraint", "subject": "Launch", "relation": "CONSTRAINED_BY", "object": "Six-week delivery window", "confidence": 0.95, "importance": 0.94, "evidence": "The launch deadline is six weeks away."},
            {"memory_type": "fact", "subject": "Enterprise customers", "relation": "REPORT", "object": "Complex permissions setup", "confidence": 0.89, "importance": 0.90, "evidence": "Interviews repeatedly mention permissions setup."},
            {"memory_type": "project", "subject": "Team", "relation": "WORKED_ON", "object": "Guided setup wizard", "confidence": 0.91, "importance": 0.84, "evidence": "The team prototyped a setup wizard."},
        ],
    },
    "Travel Planner": {
        "workspace": {
            "id": "demo_travel_planner",
            "name": "Travel Planner",
            "description": "A fictional travel workspace tracking destinations, companions, transport preferences, budget, pace, and changing plans.",
            "scenario": "Travel Planner",
        },
        "display_title": "Travel Planner Workspace",
        "scenario_tags": ["Travel preferences", "Companions and budget", "Changing plans"],
        "seed_version": "v2",
        "role_prompt": (
            "Act as a practical travel planner. Prioritize destination preferences, budget, companions, "
            "pace, transport, temporal constraints, and changes across the conversation."
        ),
        "memory_priorities": ["preference", "constraint", "goal", "event", "fact"],
        "demo_prompts": [
            "Suggest a three-day city trip that fits what you remember.",
            "My companion now wants one major museum visit, but not every day.",
            "I would accept one short flight if it saves a full day of travel.",
        ],
        "memories": [
            {"memory_type": "preference", "subject": "User", "relation": "PREFERS", "object": "Quiet historic neighborhoods", "confidence": 0.94, "importance": 0.90, "evidence": "I enjoy quiet, historic areas."},
            {"memory_type": "preference", "subject": "User", "relation": "PREFERS", "object": "Rail travel", "confidence": 0.88, "importance": 0.74, "evidence": "I prefer trains to short flights."},
            {"memory_type": "constraint", "subject": "Trip", "relation": "CONSTRAINED_BY", "object": "Moderate budget", "confidence": 0.92, "importance": 0.87, "evidence": "The trip should stay within a moderate budget."},
            {"memory_type": "fact", "subject": "Companion", "relation": "DISLIKES", "object": "Long museum visits", "confidence": 0.90, "importance": 0.79, "evidence": "My companion dislikes spending hours in museums."},
            {"memory_type": "goal", "subject": "User", "relation": "HAS_GOAL", "object": "Balance culture and relaxation", "confidence": 0.95, "importance": 0.91, "evidence": "I want culture without an exhausting itinerary."},
        ],
    },
}
