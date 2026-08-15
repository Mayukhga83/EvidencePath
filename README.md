# EvidencePath v0.3.3 — Research-Ready Language

**Decision-aware information retrieval and evidence tracking for AI agents.** A Streamlit research workbench built in Python, with optional server-managed OpenAI claim extraction.

**In plain language:** EvidencePath reads supplier documents, records what they say, and checks which missing facts could change a decision. It then suggests whether to read another passage, ask for clarification, or stop. Its example rules are fictional and are **not legal compliance advice**.

**Research focus:** Hybrid retrieval · Source-grounded claim extraction · Evidence provenance · Deterministic decision sufficiency · Agent evaluation.

### Quick start in the UI

1. Open **Case Workbench** and select **Sample documents**.
2. Read the fictional supplier policy.
3. Click **Check next passage** or **Run automatically**.
4. Open **Evidence Explorer** to inspect supporting quotes, conflicts and what-if outcomes.
5. Open **Compare methods** to inspect the controlled benchmark and error–coverage trade-off.
6. Open **About the research** for technical design, reproducibility and limitations.

### What V0.3.3 changes

This is a **writing and presentation refinement** of V0.3.2. Everyday instructions remain simple, while retrieval settings, provenance, agent traces and evaluation labels use accurate engineering terminology with short explanations. The research page presents the actual pipeline and limitations. The only code-behaviour change fixes an existing uninitialised action-trace table on first load; retrieval, extraction, rules, benchmarks and saved results remain unchanged.

---


The public demo uses **fictional supplier-approval policies**, not the EU AI Act or real legal compliance standards. It does **not** certify suppliers, give legal advice, or independently verify source statements.

## What's in V3

- **01 / Case Workbench:** one document-to-decision flow for example files or PDF/TXT/MD uploads; automatic or step-by-step evidence acquisition, manual clarification, **opt-in review of remaining passages after the automatic agent stops**, visible agent trace.
- **02 / Evidence Explorer:** evidence ledger with verbatim source passages, document/page provenance, conflicts, evidence graph, and **What Would Change This Decision?** counterfactual explorer.
- **03 / Evaluation Studio:** the preserved V1 synthetic acquisition benchmark plus a **new V3 passage-noise stress test** comparing static, retrieve-first and decision-aware strategies (no LLM judge). Interactive re-runs, plots, case-level CSV export.
- **04 / About the research:** research question, algorithms, evaluation assumptions, reproducibility and limitations.
- **Exports:** Markdown assessment, JSON audit and evidence ledger CSV (can contain sensitive excerpts; inspect before sharing).
- **LLM extraction:** Pydantic structured outputs + strict verbatim quotation checks. Optional neural retrieval and cross-encoder reranking. Offline pattern extraction remains available without any API key.
- **PaperMind-aligned design:** white/navy/blue styling, spacious hero, author card, rounded panels.

> **What changed from V2?** V3 unifies the document and case workflows and moves OpenAI credentials entirely to server configuration. V2's option to paste a personal key into the interface has been removed. Prior deterministic policy engine, sample documents and V1 benchmark are retained.

## Run locally in VS Code (Windows PowerShell)

Install Python 3.10–3.12, then extract the ZIP and open the `EvidencePath_v3` folder in VS Code.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open **http://localhost:8501**. Or double-click `start_windows.bat` (first launch installs dependencies).

On Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**No API key is necessary to explore the entire offline demo.**

### Enable OpenAI-powered extraction (one-time SERVER configuration)

**Visitors never need to enter an API key.** The *app operator* must supply an OpenAI API key once, on the server or local computer, to enable Live OpenAI mode. Do not add real credentials to Python source or GitHub.

**Local option A: environment variable (PowerShell):**

```powershell
$env:OPENAI_API_KEY = "YOUR_PRIVATE_KEY"
python -m streamlit run app.py
```

**Local option B: Streamlit secrets (recommended):** copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, replace placeholder with your own credential and restart Streamlit. The `secrets.toml` path is ignored by Git.

**Streamlit Community Cloud:** App → Settings → Secrets, add:

```toml
OPENAI_API_KEY = "YOUR_PRIVATE_KEY"
```

The credential stays server-side; do **not** paste it into the public application, README, commit or client UI. `EP_OPENAI_MODEL` can optionally select the deployed extraction model (default `gpt-4.1-mini`). The selected model must support structured output and be available to your account.

**Live analysis sends selected document passages to the OpenAI API**, so use only documents you have permission to process. Uploaded files are held in Streamlit session memory; this app does not persist their contents to its database. Review OpenAI's applicable API data policies and your organisation's requirements.

### Best-effort live-demo safeguards

- Maximum 6 upload files, 8 MB each, 40 PDF pages per file, and 300 text passages per session.
- Only the currently inspected passage (up to 5,500 characters) is submitted to the API, with up to 1,200 output tokens, a 25-second timeout and no automatic API retries.
- Per-session call limit **8** (adjust via `EP_PER_SESSION_CALL_LIMIT`).
- Single-instance total **75 calls/UTC day** by default (`EP_DAILY_SERVER_CALL_LIMIT`). Stored in SQLite in the operating system temporary directory; **no uploaded text or secret is stored there**.
- Counters intentionally charge attempted calls even on errors to avoid automatic expensive retries.

**Important:** session limits alone are not anti-abuse protection, and temporary local SQLite quotas can reset on container restart or be bypassed by multiple replicas. Do not publish an unlimited-use paid-API service without a durable external budget/rate-limiting gateway, authentication or spending controls, and abuse monitoring. These controls limit requests, not guarantee a monetary ceiling.

### Optional stronger retrieval

The default hybrid is **BM25 + offline LSA**. It is *not a neural embedding*. For pretrained dense retrieval and reranking:

```bash
pip install -r requirements-neural.txt
```

Select *Neural hybrid* or *Neural + cross-encoder reranker* in the sidebar. This downloads public model weights on first use; both options are slower. Neural retrieval uses MiniLM embeddings, and the reranking option adds a cross-encoder on the shortlist.

### Testing and reproducibility

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m evidencepath.benchmark --n 150 --seed 17 --output results
python -m evidencepath.stress_benchmark --n 90 --seed 23 --budget 5 --output results
```

`results/benchmark_*` are the preserved **V1 synthetic oracle** results. `results/v3_stress_*` are V3 **controlled noisy-passage variants of the three curated case templates**. The latter is not a held-out independent benchmark. Neither tests real-world compliance or validates LLM extraction on third-party documents.

**Stress comparison dimensions:** fraction of all cases correctly resolved, incorrect-decision rate over all cases, decision coverage, mean passage inspections and whether contradictions were surfaced. Static RAG has a fixed two-passage cap; other strategies share a maximum inspection budget. No hidden supplier answers are exposed to the decision agent. An oracle is used only for scoring.

### Architectural modules

```text
app.py                        Unified four-tab Streamlit UI
 evidencepath/
   document_lab.py            PDF/text chunking, retrieval, claim extraction and ledger
   counterfactual.py          Exact what-if decision outcomes
   runtime.py                 Server credentials + best-effort quota
   reporting.py               Markdown/JSON reports
   stress_benchmark.py        V3 seeded text-perturbation benchmark
   agent.py                   Preserved V1 synthetic agent
   logic.py                   Exact Boolean decision sufficiency
   retrieval.py               Offline BM25/LSA ranking
   models.py, cases.py        Typed rule model and fictional cases
 results/                     Reproducible experiment outputs
 tests/                       Unit and integration tests
```

## Research limitations and design integrity

- Source-anchored quotation is **not proof of factual correctness**. Contradictory documents are never resolved just by majority vote.
- The core policy rules are **hand-authored Boolean simplifications**. AI does not automatically derive trustworthy legal policy logic from arbitrary uploads.
- The exact rule evaluator may stop with a provisional decision before every uninspected contradictory passage has been found; best-effort cross-checking does not guarantee contradiction completeness. **Use the Continue evidence review control** in Case Workbench to inspect remaining passages without resetting. This does not affect automatic acquisition benchmark logic.
- The offline extractor uses **narrow patterns** and may miss paraphrases, negation or multilingual source statements. No universal document understanding or OCR is claimed.
- The V3 stress suite is a synthetic engineering diagnostic, not an independent scientific benchmark; surprising failure cases are valuable and displayed.
- The value-of-information acquisition policy remains heuristic, not a learned optimal planner. Do not claim scientific novelty or superiority without broader experiments.
- This tool does not provide real compliance determinations, professional legal advice, or security certification.

**Licence:** MIT (`LICENSE`).

## v0.3.1 patch: optional post-decision evidence review

After the automatic agent determines an outcome, the Case Workbench now displays how many passages remain uninspected and offers an expanded **Continue evidence review** section. You can choose any remaining passage and inspect it without resetting the current evidence session. If a new source contradicts an earlier extracted fact, the evidence ledger and policy result are recomputed; a clarification may become necessary.

The automatic `next_action` planner still stops at decision sufficiency; manual source auditing is a separate action, and is logged as `User-requested audit`. Each OpenAI-powered inspection still consumes one permitted live call and is subject to configured quotas. A full source audit does not independently verify supplier claims.
