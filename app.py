"""EvidencePath v0.3.0 · Streamlit interface. Start: streamlit run app.py.

No visitor-entered API credentials. Uploaded files remain in the current
Streamlit session (RAM); only selected passage text is sent to OpenAI in live
mode. Do not upload data you lack permission to process.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import pandas as pd
import streamlit as st

from evidencepath import __version__
from evidencepath.cases import curated_cases
from evidencepath.document_lab import (
    start_session, uploaded_segments, next_action, inspect_segment,
    add_clarification, ledger_rows, ranked_segments, remaining_passages, manual_review_action,
)
from evidencepath.logic import decision_snapshot
from evidencepath.graph import to_dot
from evidencepath.counterfactual import alternatives
from evidencepath.reporting import report_json, report_markdown
from evidencepath.runtime import (
    server_key, reserve_live_call, PER_SESSION_CALL_LIMIT,
    MAX_AGENT_STEPS, MODEL_DEFAULT,
)
from evidencepath.stress_benchmark import run_stress_benchmark
from evidencepath.benchmark import run_benchmark
from evidencepath.ui import (
    APP_CSS, render_header, render_author_card, render_footer,
    render_policy, render_summary, render_section,
)

st.set_page_config(page_title="EvidencePath | Evidence-Aware AI Research Workbench", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS,unsafe_allow_html=True)

CASES=curated_cases()
CASE_BY_ID={c.id:c for c in CASES}
KEY=server_key(st.secrets)
KEY_READY=bool(KEY) and not KEY.startswith("REPLACE_")

# ---------------------------------------------------------------------
# Global workspace controls
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("### EvidencePath")
    st.caption(f"v{__version__} · Evidence-aware AI research demo")
    st.divider()
    selected=st.selectbox("Choose an assessment case",list(CASE_BY_ID),format_func=lambda k:CASE_BY_ID[k].title,key="v3_case")
    source=st.radio("Where should evidence come from?",["Sample documents","My documents"],key="v3_source")
    extract_options=["Live OpenAI","Offline text matching"] if KEY_READY else ["Offline text matching"]
    extraction=st.selectbox("Claim extraction method",extract_options,key="v3_extractor",help="Extract candidate facts from document passages. OpenAI uses structured outputs with an exact-quote check; the offline option uses limited text patterns.")
    rank_label=st.selectbox("Retrieval method",["Hybrid · BM25 + LSA (offline)","Keyword · BM25 (offline)","Neural hybrid · embeddings (optional)","Neural hybrid + reranker (optional)"],key="v3_retrieval",help="Retrieval ranks document passages by relevance. The default combines BM25 keywords with LSA semantic similarity. Neural options require additional packages.")
    rank_mode={"Hybrid · BM25 + LSA (offline)":"hybrid","Keyword · BM25 (offline)":"bm25","Neural hybrid · embeddings (optional)":"neural","Neural hybrid + reranker (optional)":"neural-rerank"}[rank_label]
    st.divider()
    if KEY_READY:
        st.success("OpenAI claim extraction is available")
    else:
        st.info("Offline extraction is ready. Live OpenAI analysis is not enabled on this server; you can still explore every sample case.")
    st.caption("BM25 + LSA works offline. Neural embeddings and reranking require optional models and may download weights on first use.")
    st.caption(f"Live AI requests used: {st.session_state.get('v3_calls',0)} of {PER_SESSION_CALL_LIMIT}")
    st.caption("Research prototype using fictional policies. Source quotations are not independent verification or supplier certification.")

render_header()
render_author_card()
with st.expander("How EvidencePath works", expanded=False):
    st.markdown("""**1. Choose a case.** Use the sample documents or add your own PDF or text files.

**2. Read the example policy.** This is a **fictional supplier rule**, not a legal standard.

**3. Inspect evidence.** Click **Check next passage** or **Run automatically**. Retrieval finds relevant text, and claim extraction identifies possible answers.

**4. Review missing facts.** The decision engine checks whether an unknown fact could change the result. Conflicting claims remain visible.

**5. Explore the sources.** Open the **Evidence Explorer** to inspect exact quotations and test what-if outcomes. Use **Compare methods** to see benchmark results.

**What makes this an AI research prototype?** It combines retrieval, source-grounded claim extraction, a deterministic policy checker and an information-seeking agent. Their limitations are explained under **About the research**.

**Important:** An exact quote proves what a document states, not whether it is true. Uploaded documents remain in session memory; selected passages go to OpenAI only in live mode. Do not upload information you lack permission to process.""")


# ---------------------------------------------------------------------
# Shared document state, isolated by document-content fingerprint
# ---------------------------------------------------------------------
files=[]
if source=="My documents":
    files=st.file_uploader("Add supplier documents (PDF, TXT, MD)",type=["pdf","txt","md"],accept_multiple_files=True,key="v3_uploads") or []
    st.caption("Up to 6 files, 8 MB each, and 40 PDF pages per file. Scanned PDFs cannot be read here.")
    if len(files)>6: st.error("Please add no more than 6 files."); st.stop()
    if not files: st.info("Add a document to begin, or choose Sample documents.")

fingerprint=hashlib.sha256(f"{selected}:{source}".encode())
for f in files:
    fingerprint.update(f.name.encode()); fingerprint.update(f.getvalue())
signature=fingerprint.hexdigest()
if (source=="Sample documents" or files) and st.session_state.get("v3_signature")!=signature:
    try:
        segments=None
        if files:
            segments=[]
            for i,f in enumerate(files):
                segments.extend(uploaded_segments(f.name,f.getvalue(),f"UPLOAD-{i+1}"))
            if len(segments)>300: raise ValueError("These documents are too long. Please upload shorter files (up to 300 text sections).")
            if not segments: raise ValueError("These files do not contain readable text")
        st.session_state["v3_session"]=start_session(selected,segments)
        st.session_state["v3_signature"]=signature
    except Exception as exc:
        st.error(f"Could not read the files: {exc}")
        st.stop()
session=st.session_state.get("v3_session") if (source=="Sample documents" or files) else None


def perform_inspection(action):
    """Charge quota before live model call, never store secret in UI state."""
    if action.kind!='search': return []
    if extraction=="Live OpenAI":
        previous=int(st.session_state.get("v3_calls",0))
        st.session_state["v3_calls"]=reserve_live_call(previous)
        claims=inspect_segment(session,action.segment_id,'openai',KEY,MODEL_DEFAULT)
    else:
        claims=inspect_segment(session,action.segment_id,'offline')
    if session.events:
        session.events[-1]["Reason"]=action.reason
    return claims


def step_auto():
    count=0
    for _ in range(MAX_AGENT_STEPS):
        action=next_action(session,rank_mode)
        if action.kind!='search': break
        perform_inspection(action)
        count+=1
    return count

case_tab,explorer_tab,evaluation_tab,research_tab=st.tabs([
    "01 · Case Workbench", "02 · Evidence Explorer", "03 · Compare methods", "04 · About the research"
])

with case_tab:
    render_section("Case Workbench","Review documents, track missing evidence, and see how the agent chooses its next step.")
    if session:
        snap=decision_snapshot(session.core)
        render_policy(session.case.policy_text)
        render_summary(snap['status'],len(snap['known']),len(session.case.labels),len(snap['critical']),session.cost)
        col1,col2=st.columns([1.2,1],gap='large')
        with col1:
            render_section("Evidence status","Known facts, unresolved questions, and conflicts across source documents.")
            items=[]
            for k,label in session.case.labels.items():
                value=("Yes" if snap['known'][k] else "No") if k in snap['known'] else "Conflicted" if k in snap['conflicts'] else "Unknown"
                items.append({'Question':label,'Answer':value,'May change result':"Yes" if k in snap['critical'] else "",'Source statements':len(session.core.evidence.get(k,[]))})
            st.dataframe(pd.DataFrame(items),hide_index=True,use_container_width=True)
            if snap['conflicts']:
                st.error("Documents disagree about: "+", ".join(session.case.labels[k] for k in snap['conflicts']))
            if any(len({e.value for e in ev if e.method!='manual'})>1 for ev in session.core.evidence.values()):
                st.warning("Some documents still disagree, even if you entered an answer manually. Please check which source is correct.")
            st.caption("A quote shows what a document says. It does not prove the statement is true.")
            with st.expander("Retrieval results · ranked source passages"):
                target=st.selectbox("What are you trying to check?",list(session.case.labels),format_func=lambda x:session.case.labels[x],key="v3_query")
                try:
                    ranking=ranked_segments(session.case.keywords[target],session.segments,rank_mode)
                    st.dataframe(pd.DataFrame([{'Rank':i,'Document':seg.title,'Page / section':seg.location,'Relevance score':round(score,3),'Inspected':seg.id in session.inspected} for i,(seg,score) in enumerate(ranking[:25],1)]),hide_index=True,use_container_width=True)
                    st.caption("These scores rank passages for retrieval; they are not confidence scores or proof that the passage is correct.")
                except Exception as exc:
                    st.error(f"Retrieval not available: {exc}")
        with col2:
            render_section("Agent's next step","The agent selects a passage, requests clarification, or stops when the current facts settle the example rule.")
            try: action=next_action(session,rank_mode)
            except Exception as exc:
                st.error(f"Retrieval failed: {exc}"); action=None
            if action:
                if action.kind=='stop':
                    if snap['status']=='ELIGIBLE': st.success("Meets the example rule based on documents read so far")
                    elif snap['status']=='NOT ELIGIBLE': st.error("Does not meet the example rule based on documents read so far")
                    else: st.warning("Not enough evidence. Ask someone to review.")
                    st.caption(action.reason)
                elif action.kind=='search':
                    seg=next(s for s in session.segments if s.id==action.segment_id)
                    st.info(f"**Read next:** {seg.title} · {seg.location}")
                    st.write(action.reason)
                    with st.expander("Preview this passage"):
                        st.code(seg.text[:1800],language='text')
                else:
                    st.warning("A person needs to clarify this")
                    st.write(action.reason)
                if action.kind=='search':
                    l,r=st.columns(2)
                    with l:
                        if st.button("Check next passage",type="primary",use_container_width=True):
                            try:
                                perform_inspection(action)
                                st.rerun()
                            except Exception as exc:
                                st.error("AI analysis failed. Nothing was changed." if extraction=="Live OpenAI" else f"Could not read this passage: {exc}")
                    with r:
                        if st.button("Run automatically",use_container_width=True):
                            try:
                                step_auto()
                                st.rerun()
                            except Exception as exc:
                                st.error("The run stopped unexpectedly. Your results are saved for this session. Try Offline text matching." if extraction=="Live OpenAI" else str(exc))
                if action.kind=='clarify' and action.fact_key:
                    with st.form('v3_clarify'):
                        st.markdown(f"**{session.case.labels[action.fact_key]}**")
                        answer=st.radio("Your answer (not yet verified)",['Yes','No'],horizontal=True)
                        if st.form_submit_button('Save answer',type='primary'):
                            add_clarification(session,action.fact_key,answer=='Yes')
                            st.rerun()
                # Automatic stopping means the CURRENT observed facts determine
                # the fictional policy outcome. It does not mean every available
                # document has been checked or could not disagree with earlier ones.
                pending = remaining_passages(session)
                if pending:
                    if action.kind == 'stop':
                        st.warning(
                            f"**{len(pending)} passage(s) still unread.** "
                            "The result may change if you read more documents. "
                            "You can check the rest below."
                        )
                    with st.expander(
                        f"Check more documents · {len(pending)} remaining",
                        expanded=(action.kind == 'stop'),
                    ):
                        st.caption(
                            "You can keep reading even after the app stops. "
                            "A new passage may confirm or change the result."
                        )
                        chosen = st.selectbox(
                            "Choose an unread passage",
                            [p.id for p in pending],
                            format_func=lambda passage_id: next(
                                f"{p.title} · {p.location} · {p.id}" for p in pending
                                if p.id == passage_id
                            ),
                            key=f"v3_extra_review_{signature[:12]}",
                        )
                        chosen_passage = next(p for p in pending if p.id == chosen)
                        st.caption(chosen_passage.text[:240] + ('…' if len(chosen_passage.text) > 240 else ''))
                        if st.button(
                            "Check this passage",
                            type='secondary',
                            use_container_width=True,
                            key='v3_extra_review_run',
                        ):
                            try:
                                audit_action = manual_review_action(session, chosen)
                                perform_inspection(audit_action)
                                if session.events:
                                    session.events[-1]['Action'] = 'Extra document check'
                                st.rerun()
                            except Exception as exc:
                                st.error(
                                    "Could not check this passage. Previous results are still here. "
                                    "Try Offline text matching if AI is unavailable."
                                    if extraction == 'Live OpenAI'
                                    else f"Could not review passage: {exc}"
                                )
                else:
                    st.caption("All passages have been checked. Reset the case to start over.")
                if st.button("Start this case again",use_container_width=True):
                    st.session_state.pop('v3_signature',None)
                    st.rerun()
                st.caption(f"{len(session.inspected)} / {len(session.segments)} passages checked · {len(session.events)} steps taken")
        st.divider()
        render_section("Agent trace","Inspect each document-reading or clarification action and its effect on the decision.")
        if session.events:
            trace = pd.DataFrame(session.events).rename(columns={
                'Step':'Step', 'Action':'What happened', 'Target':'Document / topic',
                'Evidence':'Statements found', 'Cost':'Effort points',
                'Status':'Result', 'Reason':'Why',
            })
            if 'Result' in trace.columns:
                trace['Result'] = trace['Result'].replace({
                    'ELIGIBLE':'Meets rule', 'NOT ELIGIBLE':'Does not meet rule',
                    'UNRESOLVED':'Needs more evidence',
                })
            if 'What happened' in trace.columns:
                trace['What happened'] = trace['What happened'].replace({
                    'Inspect source':'Checked document',
                    'Manual clarification':'Saved a manual answer',
                })
            st.dataframe(trace,use_container_width=True,hide_index=True)
        else:
            st.info("Inspect a passage to see the agent's steps here.")
    else:
        st.info("Choose Sample documents or add your own files to begin.")

with explorer_tab:
    render_section("Evidence Explorer","Trace extracted claims to their exact sources, inspect contradictions, and explore what-if decisions.")
    if session:
        rows=ledger_rows(session)
        left,right=st.columns([1.2,1],gap="large")
        with left:
            render_section("Evidence ledger","Each extracted claim includes its source, exact passage, and any conflicting evidence.")
            if rows:
                plain_rows = pd.DataFrame(rows).rename(columns={
                    "Fact": "Question", "Value": "Answer", "Location": "Where", "Quote": "Document says",
                    "Method": "Read using", "Verbatim grounded": "Quote found in text",
                    "Decision-critical": "May change result", "Unresolved conflict": "Unresolved disagreement",
                    "Source disagreement": "Documents disagree",
                })
                plain_rows['Read using'] = plain_rows['Read using'].replace({'offline-pattern':'Offline text matching','llm-structured / exact-span':'Live AI text analysis','manual':'Manual answer'})
                st.dataframe(plain_rows,hide_index=True,use_container_width=True)
                for i,r in enumerate(rows):
                    with st.expander(f"{r['Fact']} · {r['Value']} · {r['Source']} · {r['Location']}"):
                        st.code(r['Quote'],language='text')
                        st.caption(f"Read using: { {'offline-pattern':'Offline text matching','llm-structured / exact-span':'Live AI text analysis','manual':'Manual answer'}.get(r['Method'],r['Method']) } · Exact quote found: {r['Verbatim grounded']} · Documents disagree: {r['Source disagreement']}")
            else:
                st.info("No statements yet. Check a passage in the first tab.")
        with right:
            render_section("What could change the result?","Counterfactual check: try a possible answer and see whether the decision changes. This does not add evidence.")
            key=st.selectbox("Choose a question",list(session.case.labels),format_func=lambda k:session.case.labels[k],key='v3_what_if')
            cf=alternatives(session.core,key)
            st.caption(f"Current answer: **{ {'UNKNOWN':'Not known', 'CONFLICT':'Documents disagree'}.get(cf['current'],cf['current']) }**")
            a,b=st.columns(2)
            with a: st.metric("If Yes",{'ELIGIBLE':'Meets rule','NOT ELIGIBLE':'Does not meet rule','UNRESOLVED':'Needs more evidence'}.get(cf['if_yes'],cf['if_yes']))
            with b: st.metric("If No",{'ELIGIBLE':'Meets rule','NOT ELIGIBLE':'Does not meet rule','UNRESOLVED':'Needs more evidence'}.get(cf['if_no'],cf['if_no']))
            if cf['changes_decision']: st.info("This answer could change the result.")
            else: st.caption("Changing this answer alone would not settle the result.")
            if cf['other_unknowns_remaining']: st.caption("Other questions still need answers: "+", ".join(session.case.labels.get(k,k) for k in cf['other_unknowns_remaining']))
            st.caption("These are examples, not proof or an approval recommendation.")
        st.divider()
        with st.expander("Policy and evidence graph",expanded=True):
            st.graphviz_chart(to_dot(session.core),use_container_width=True)
        with st.expander("Download the results",expanded=False):
            st.warning("Downloads may include text from your documents. Check before sharing.")
            st.download_button("Download readable report",report_markdown(session),"EvidencePath_assessment.md",mime='text/markdown')
            st.download_button("Download full data (JSON)",report_json(session),"EvidencePath_assessment.json",mime='application/json')
            if rows: st.download_button("Download statements (CSV)",pd.DataFrame(rows).to_csv(index=False).encode('utf-8'),"EvidencePath_ledger.csv",mime='text/csv')
    else: st.info("Open a case in the first tab to begin.")

with evaluation_tab:
    render_section("Compare methods","Controlled benchmarks compare decision accuracy, coverage, evidence cost and contradictions. All cases are synthetic.")
    suite=st.radio("Benchmark suite",["V3 · Noisy-passage evaluation","V1 · Structured-fact baseline"],horizontal=True)
    if suite.startswith("V3"):
        st.caption("V3 stress test: perturb passages in three fictional policy templates, then compare static retrieval, retrieve-first search and decision-aware search. Not an independent legal or supplier benchmark.")
        if 'v3_stress_results' in st.session_state:
            raw,summary=st.session_state['v3_stress_results']
            st.caption('Results from your current test')
        else:
            base=Path(__file__).parent/'results'
            raw=pd.read_csv(base/'v3_stress_raw.csv')
            summary=pd.read_csv(base/'v3_stress_summary.csv')
            st.caption('Saved reference run: 90 synthetic cases · fixed seed 23 · up to 5 passage inspections')
        c1,c2,c3=st.columns(3)
        with c1: n=st.slider('Synthetic cases',30,180,90,30)
        with c2: seed=st.number_input('Random seed (reproducibility)',0,99999,23)
        with c3:
            budget=st.slider('Evidence budget · max passages',1,10,5)
            if st.button('Run benchmark',use_container_width=True):
                with st.spinner('Running the test…'):
                    st.session_state['v3_stress_results']=run_stress_benchmark(n,int(seed),budget)
                st.rerun()
        metrics=summary.copy()
        for col in ['coverage','correctly_resolved','incorrect','conflict_flagged']:
            metrics[col]=(metrics[col]*100).round(1)
        metrics=metrics.rename(columns={'strategy':'Strategy','cases':'Cases','coverage':'Resolved %','correctly_resolved':'Correctly resolved %','incorrect':'Incorrect decision %','mean_passages':'Mean passages','conflict_flagged':'Conflict flagged %','mean_cost':'Mean cost'})
        plain_metrics = metrics.rename(columns={
            'Strategy':'Retrieval / agent strategy', 'Cases':'Test cases', 'Resolved %':'Decision coverage %',
            'Correctly resolved %':'Correct decisions %', 'Incorrect decision %':'Incorrect decisions %',
            'Mean passages':'Passages inspected (avg)', 'Conflict flagged %':'Conflicts flagged %',
            'Mean cost':'Acquisition cost (avg)',
        })
        plain_metrics['Retrieval / agent strategy'] = plain_metrics['Retrieval / agent strategy'].replace({'static_two':'Static (first 2 passages)','retrieve_first':'Retrieve-first','adaptive':'Decision-aware acquisition'})
        st.dataframe(plain_metrics.round(2),hide_index=True,use_container_width=True)
        st.caption("Decision coverage = percentage with a Yes/No outcome. Correct/incorrect decisions use **all cases** as the denominator; abstentions count as neither. Acquisition cost is simulated effort, not time or money.")
        a,b=st.columns(2)
        with a:
            st.markdown('**Correct decisions · % of all cases**')
            st.bar_chart(metrics.set_index('Strategy')['Correctly resolved %'])
        with b:
            st.markdown('**Incorrect decisions · % of all cases**')
            st.bar_chart(metrics.set_index('Strategy')['Incorrect decision %'])
        st.info("**Research trade-off:** A cautious agent may reduce incorrect decisions yet leave more cases unresolved. Compare error rate **and** coverage; neither alone shows which strategy is best.")
        with st.expander('Inspect failure cases'):
            wrong=raw[raw['incorrect']==1]
            if not wrong.empty: st.dataframe(wrong.head(40),hide_index=True,use_container_width=True)
            else: st.caption('No wrong answers in this test run.')
        st.download_button('Download test results (CSV)',raw.to_csv(index=False),'EvidencePath_v3_stress.csv',mime='text/csv')
        with st.expander('Benchmark design and limitations'):
            st.markdown('**Setup:** Three handcrafted fictional policy templates generate perturbed document passages with omissions, irrelevant text and occasional contradictory claims. A deterministic oracle scores outcomes; no LLM judge is used.\n\n**Baselines:** Static retrieval reads the first two passages. Retrieve-first and decision-aware methods use the selected inspection budget. Different budgets must be considered when interpreting results.\n\n**Limits:** Variants of three templates are not independent real-world cases. This does not measure OpenAI extraction quality, legal reasoning, or performance on unseen policies.')
    else:
        st.caption('V1 baseline uses scripted hidden facts and a deterministic rule oracle; it does not evaluate extraction from raw documents.')
        if 'v3_old_benchmark' in st.session_state:
            raw,summary=st.session_state['v3_old_benchmark']
        else:
            root=Path(__file__).parent/'results'
            raw=pd.read_csv(root/'benchmark_raw.csv')
            summary=pd.read_csv(root/'benchmark_summary.csv')
        c1,c2=st.columns(2)
        with c1: n_old=st.slider('Cases',15,300,60,15)
        with c2:
            if st.button('Run basic test'):
                st.session_state['v3_old_benchmark']=run_benchmark(n_old,17)
                st.rerun()
        st.dataframe(summary.rename(columns={'strategy':'Method','correctly_resolved':'Right answers','mean_cost':'Average effort'}),hide_index=True,use_container_width=True)
        st.download_button('Download basic test results',raw.to_csv(index=False),'EvidencePath_v1_benchmark.csv',mime='text/csv')

with research_tab:
    render_section('About the research', 'The research question, system design, benchmarks and honest limitations behind EvidencePath.')
    st.markdown("""### Research question

**Can an information-seeking agent identify which missing evidence could change a decision and acquire it without unnecessary document searches?**

Traditional retrieval ranks passages by relevance. EvidencePath also tracks whether the *facts those passages provide* are sufficient for a simple decision. This difference matters when a source is missing, two sources conflict, or an unknown fact would not affect the outcome.

### System design

**Document text → passage retrieval → claim extraction → evidence ledger → decision check → next agent action**

- **Hybrid retrieval:** BM25 keyword matching plus offline LSA similarity by default. Optional neural embeddings and cross-encoder reranking help test stronger ranking methods.
- **Source-grounded extraction:** Offline text patterns or optional OpenAI structured outputs propose fact values. An LLM claim must include a verbatim quotation from the inspected passage.
- **Evidence provenance:** Each claim retains its source and passage. Contradictory claims remain visible instead of being resolved by a majority vote.
- **Deterministic decision check:** A simple Boolean policy model evaluates whether currently unresolved facts can change the result.
- **Evidence-acquisition agent:** The controller retrieves another passage, requests clarification or stops. A user can still review unread passages after automatic stopping.

### How we evaluate it

The **V1 benchmark** tests acquiring predefined facts. The **V3 stress benchmark** tests retrieval and decisions over noisy passages generated from three fictional supplier scenarios. Methods are compared by **decision coverage, correct and incorrect decision rates, evidence cost and conflict detection**. A fixed oracle scores the synthetic cases, not an LLM judge.

The useful result is not simply the highest number of completed cases. A method may answer more questions **while also making more incorrect decisions**. The evaluation makes this accuracy–coverage trade-off visible.

### Scope and limitations

**This is a research prototype, not a compliance certification system.** The policies are fictional, and the Boolean rules are authored in advance. An exact quote verifies where a claim came from, **not whether the claim is true**. Unread documents can still contain contradictions, and the benchmark does not establish legal reliability or generalisation to unseen domains.
""")
    with st.expander('Technical details · algorithms and reproducibility', expanded=False):
        st.markdown("""**Decision sufficiency:** For unresolved Boolean policy variables, the checker enumerates remaining assignments. If all assignments produce the same policy result, the observed state is sufficient *under the simplified rule and sources inspected*. It is not a guarantee that later evidence cannot contradict an observed fact.

**Retrieval:** BM25 + latent semantic analysis (LSA) is the offline default. Optional pretrained sentence embeddings and cross-encoder reranking require separate dependencies. Retrieval score indicates relevance, not certainty.

**Claim processing:** Optional OpenAI extraction uses structured outputs and an exact-quote guard. Extracted statements are candidates; no independent factual validation or legal interpretation is performed.

**Agent policy:** A heuristic selects document inspection or clarification based on current decision-critical gaps. It is not a learned optimal value-of-information policy. Automatic stopping and user-requested full review are separate.

**Evaluation setup:** The original V1 suite exposes scripted hidden facts to a deterministic oracle, not the agent. V3 adds passage omission, distractors and contradictions to three handcrafted templates. Static retrieval inspects two passages; the other strategies share a configured maximum. This is a controlled engineering diagnostic, not an independent external benchmark.

**Privacy:** Server-side API credentials are never requested from visitors. Selected passages are sent to OpenAI only in live mode. Local usage quotas are best-effort and do not guarantee spending caps.

**Reproduce experiments:**
```bash
python -m evidencepath.benchmark --n 150 --seed 17 --output results
python -m evidencepath.stress_benchmark --n 90 --seed 23 --budget 5 --output results
python -m pytest -q
```
""")
    with st.expander('Quick glossary', expanded=False):
        st.markdown("""- **Retrieval:** Finding relevant passages in documents.
- **Hybrid retrieval:** Combining keyword and semantic similarity for passage ranking.
- **Claim extraction:** Turning a statement in text into a proposed structured fact.
- **Provenance:** Recording where a statement came from, including its exact quotation.
- **Decision sufficiency:** Checking whether unresolved facts can change a simplified rule-based result.
- **Agent trace:** A record of which actions the system took and why.
- **Decision coverage:** The share of test cases that receive a Yes/No conclusion, excluding abstentions.
""")

render_footer()
