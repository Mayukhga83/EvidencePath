"""Curated fictional policy cases and a seeded synthetic benchmark generator."""
from __future__ import annotations
import random
from .models import Case, Document, fact, AND, OR, NOT


def curated_cases() -> list[Case]:
    cloud = Case(
        id="cloud-host", title="Cloud storage: where is the data kept?",
        description="An organisation is assessing a cloud supplier to store confidential client files. Internal policy requires encryption, a current security review, and approved hosting when confidential information is processed.",
        policy_text="Under this example rule, suppliers that do not handle confidential data can be approved. Otherwise, they must encrypt stored data, pass a security review, and keep data in an approved location. Company revenue does not matter.",
        rule=OR(NOT(fact("confidential")), AND(fact("encryption"), fact("review"), fact("hosting"))),
        labels={"confidential":"Handles confidential information", "encryption":"Encrypts stored data", "review":"Security review completed", "hosting":"Stores data in an approved location", "revenue":"Annual revenue over €1 million"},
        keywords={"confidential":"client files confidentiality data sensitivity", "encryption":"encryption at rest key management storage", "review":"security assessment audit review certification", "hosting":"hosting location region data residency processing Frankfurt", "revenue":"annual financial revenue turnover"},
        initial={"confidential":True,"encryption":True,"review":True},
        documents=(
            Document("CH-1", "Cloud hosting and processing agreement", "Production client data is stored and processed in Frankfurt, Germany. The designated region is within the organisation's approved hosting locations. Regional failover stays in Germany.", {"hosting":True}),
            Document("CH-2", "Encryption architecture", "Stored files are protected using AES-256 encryption at rest with managed keys. This document covers encryption and storage controls.", {"encryption":True}),
            Document("CH-3", "Financial overview", "Annual turnover revenue exceeds one million euro. This commercial report has no security residency information.", {"revenue":True}),
            Document("CH-4", "Supplier overview", "The supplier operates a European cloud service for confidential client files. Its customer support is available in multiple languages.", {"confidential":True}),
        ),
        supplier_answers={"confidential":True,"encryption":True,"review":True,"hosting":True,"revenue":True},
    )
    exemption = Case(
        id="sandbox-exemption", title="Test environment: no further checks needed",
        description="A prospective analytics supplier uses a sandbox for test data only. Its unknown production controls look concerning, but the internal policy explicitly exempts this type of sandbox.",
        policy_text="Under this example rule, a supplier used only for testing can be approved. Otherwise, it needs access controls, activity logs, and approved subcontractors. Company size does not matter.",
        rule=OR(fact("sandbox"), AND(fact("access"),fact("logs"),fact("subprocessors"))),
        labels={"sandbox":"Used only for testing", "access":"Access controls in place", "logs":"Activity logging enabled", "subprocessors":"Subcontractors approved", "headcount":"Supplier has over 100 employees"},
        keywords={"sandbox":"testing sandbox non production isolated synthetic", "access":"access control authentication", "logs":"audit logging events history", "subprocessors":"subprocessor vendor third-party register", "headcount":"employees headcount staff count"},
        initial={"sandbox":True},
        documents=(
            Document("SB-1", "Sandbox deployment note", "This is a fully isolated sandbox used only for tests with synthetic data. There is no production integration.", {"sandbox":True}),
            Document("SB-2", "Security questionnaire", "The vendor uses centralised identity access control, audit logging and a listed set of approved subcontractors.", {"access":True,"logs":True,"subprocessors":True}),
            Document("SB-3", "Company profile", "The firm employs 180 people worldwide.", {"headcount":True}),
        ),
        supplier_answers={"sandbox":True,"access":True,"logs":True,"subprocessors":True,"headcount":True},
    )
    conflict = Case(
        id="contradictory-evidence", title="Software supplier: documents disagree",
        description="A vendor's marketing security statement conflicts with a more recent audit observation. A supplier representative can clarify the unresolved control.",
        policy_text="This example rule requires encryption, a completed security review, and an approved data location. If the documents disagree about encryption, get clarification before deciding.",
        rule=AND(fact("encryption"),fact("review"),fact("hosting")),
        labels={"encryption":"Production data is encrypted", "review":"Security review completed", "hosting":"Approved data location", "employees":"Over 50 employees"},
        keywords={"encryption":"production encryption at rest storage database keys", "review":"audit security review assessment", "hosting":"data residency hosting region", "employees":"staff employees headcount"},
        initial={"review":True,"hosting":True},
        documents=(
            Document("CV-1", "Marketing security overview", "Production database encryption at rest is enabled for all customer records, according to the vendor brochure.", {"encryption":True}),
            Document("CV-2", "Independent audit excerpt", "The independent inspection reports production database encryption at rest is not enabled in the legacy processing cluster.", {"encryption":False}),
            Document("CV-3", "Organisation directory", "Company employee headcount is 240 and growing.", {"employees":True}),
        ),
        supplier_answers={"encryption":False,"review":True,"hosting":True,"employees":True},
        preloaded_documents=("CV-1", "CV-2"),
    )
    return [cloud, exemption, conflict]


TEMPLATES = [
    ("Cloud storage", "cloud", ["confidential", "encryption", "review", "hosting"],
     OR(NOT(fact("confidential")), AND(fact("encryption"),fact("review"),fact("hosting"))),
     "A supplier is eligible if it does not process confidential files, or has encryption, security review and approved hosting."),
    ("Software integration", "software", ["sandbox", "access", "logs", "subprocessors"],
     OR(fact("sandbox"), AND(fact("access"),fact("logs"),fact("subprocessors"))),
     "A non-production sandbox is eligible, or an integrated vendor must provide access control, audit logging and approved subcontractors."),
    ("Packaging audit", "packaging", ["pilot", "materials", "traceability", "report"],
     OR(fact("pilot"), AND(fact("materials"),fact("traceability"),fact("report"))),
     "A laboratory pilot is eligible, or a production supplier must verify materials, traceability and reporting."),
]

LABELS = {
    "confidential":"Handles confidential client files", "encryption":"Encryption enabled", "review":"Security review complete", "hosting":"Approved data location",
    "sandbox":"Non-production sandbox only", "access":"Access controls verified", "logs":"Audit logging enabled", "subprocessors":"Subcontractors approved",
    "pilot":"Laboratory pilot exemption applies", "materials":"Materials verified", "traceability":"Traceability records complete", "report":"Required report filed", "revenue":"Commercial revenue exceeds threshold",
}
KEYWORDS = {
    "confidential":"confidential files sensitivity", "encryption":"encryption at rest data storage", "review":"security review assessment", "hosting":"hosting data location region",
    "sandbox":"non production sandbox testing", "access":"access control authentication", "logs":"audit logs events", "subprocessors":"approved subcontractors register",
    "pilot":"laboratory pilot exemption", "materials":"material verification certification", "traceability":"product traceability chain", "report":"report submission compliance",
    "revenue":"revenue commercial turnover",
}


def generated_cases(n: int = 150, seed: int = 17) -> list[Case]:
    """Reproducible Boolean-policy testbed. Not a validated legal dataset.

    Hidden supplier answers are used ONLY when simulating clarification and
    reporting oracle outcomes, never to plan the agent's next action.
    """
    rng = random.Random(seed)
    cases: list[Case] = []
    for idx in range(n):
        title, category, vars_, rule, policy = TEMPLATES[idx % len(TEMPLATES)]
        keys = [*vars_, "revenue"]
        rng.shuffle(keys)
        labels = {k: LABELS[k] for k in keys}
        keywords = {k: KEYWORDS[k] for k in labels}
        truth = {k: rng.random() < (0.18 if k in ("sandbox","pilot") else (0.77 if k in ("encryption","review","hosting","access","logs","subprocessors","materials","traceability","report") else 0.7)) for k in labels}
        initially_seen = rng.sample(vars_, rng.choice([0,1,1,2,2,3]))
        # Distractor initially known or unknown should not drive decision-aware search.
        initial = {k: truth[k] for k in initially_seen}
        doc_entries = []
        for key in vars_:
            if key in initial or rng.random() > 0.70:
                continue
            truth_desc = "confirmed" if truth[key] else "not confirmed"
            doc_entries.append(Document(f"D{idx:03}-{key}",f"{LABELS[key]} — evidence memo",f"Supplier documentation about {KEYWORDS[key]}. Review finding: {LABELS[key]} is {truth_desc}.",{key:truth[key]}))
        doc_entries.append(Document(f"D{idx:03}-revenue", "Commercial background", "Supplier annual revenue commercial turnover information is on file.", {"revenue":truth["revenue"]}))
        rng.shuffle(doc_entries)
        cases.append(Case(
            id=f"synthetic-{idx:03}", title=f"{title} — synthetic case {idx+1}",
            description=f"Generated {category} assessment with partially observed facts and simulated supplier answers.",
            policy_text=policy,rule=rule,labels=labels,keywords=keywords,initial=initial,
            documents=tuple(doc_entries), supplier_answers=truth, category=category,
        ))
    return cases
