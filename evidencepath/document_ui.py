"""Streamlit V2 document lab. No Streamlit imports in the research core."""
from __future__ import annotations
import hashlib
import os
from html import escape
import pandas as pd
import streamlit as st
from .document_lab import (
    start_session, uploaded_segments, next_action, inspect_segment,
    add_clarification, ledger_rows, ranked_segments
)
from .cases import curated_cases
from .logic import decision_snapshot
from .graph import to_dot
from .ui import render_section, render_policy, render_summary


def render_document_lab(case_id: str):
    case = next(c for c in curated_cases() if c.id==case_id)
    render_section('Document Intelligence Lab', 'Acquire evidence from actual text, inspect supporting passages, and test decision sufficiency.')
    st.info('V2 document mode does **not** use V1 hidden assertion labels or simulated supplier answers. It extracts candidate statements from text and requires manual clarification when documents cannot resolve a fact.')
    render_policy(case.policy_text)
    p1,p2,p3=st.columns([1.2,1,1])
    with p1:
        source_mode=st.radio('Document source',['Built-in text examples','Upload my documents'],horizontal=False,key='v2_source')
    with p2:
        extraction_mode=st.selectbox('Extraction method',['Offline patterns','OpenAI (optional)'],key='v2_extractor')
    with p3:
        ranking=st.selectbox('Retrieval method',['Hybrid · BM25 + LSA','BM25 only','Neural hybrid (optional)'],key='v2_rank')
    rank_key={'Hybrid · BM25 + LSA':'hybrid','BM25 only':'bm25','Neural hybrid (optional)':'neural'}[ranking]
    st.caption('Offline patterns cover the provided supplier-policy facts only. LSA is not neural; neural retrieval and OpenAI extraction are optional installations.')
    api_key=''
    llm_model='gpt-4.1-mini'
    if extraction_mode=='OpenAI (optional)':
        st.warning('If enabled, retrieved document passages are sent to the OpenAI API. Do not upload confidential or personal documents without appropriate permission and data-handling controls.')
        api_key=st.text_input('OpenAI API key (used only for this session)',type='password',value=os.environ.get('OPENAI_API_KEY',''),key='v2_key')
        llm_model=st.text_input('OpenAI extraction model',value='gpt-4.1-mini',key='v2_model')
    uploads=[]
    if source_mode=='Upload my documents':
        st.caption('Supported: searchable PDF, UTF-8 TXT and Markdown · max 8 MB per file, 40 PDF pages. OCR for scanned PDFs is not included.')
        uploads=st.file_uploader('Supplier documents',type=['pdf','txt','md'],accept_multiple_files=True,key='v2_files') or []
        if len(uploads)>6:
            st.error('Please upload no more than 6 documents.')
            return
        if not uploads:
            st.info('Upload one or more supplier documents to activate the evidence-acquisition workbench.')
            return

    fingerprint=hashlib.sha256()
    fingerprint.update((case_id+'|'+source_mode+'|'+extraction_mode).encode())
    for f in uploads:
        fingerprint.update(f.name.encode('utf-8'))
        fingerprint.update(f.getvalue())
    signature=fingerprint.hexdigest()
    if st.session_state.get('v2_signature')!=signature:
        try:
            if source_mode=='Upload my documents':
                segments=[]
                for i,f in enumerate(uploads):
                    segments.extend(uploaded_segments(f.name,f.getvalue(),f'UP-{i+1}'))
                if not segments:
                    st.warning('No readable text extracted from these documents.')
                    return
                session=start_session(case_id,segments)
            else:
                session=start_session(case_id)
            st.session_state['v2_doc_state']=session
            st.session_state['v2_signature']=signature
        except Exception as exc:
            st.error(f'Could not read the source documents: {exc}')
            return
    session=st.session_state['v2_doc_state']
    snap=decision_snapshot(session.core)
    render_summary(snap['status'],len(snap['known']),len(case.labels),len(snap['critical']),session.cost)
    colleft,colright=st.columns([1.15,1],gap='large')
    with colleft:
        render_section('Evidence inventory','Every observed fact retains the provenance that supports the claim.')
        inv=[]
        for key,label in case.labels.items():
            value=('Yes' if snap['known'][key] else 'No') if key in snap['known'] else ('Conflicting' if key in snap['conflicts'] else 'Unknown')
            inv.append({'Fact':label,'Observed':value,'Critical':'★' if key in snap['critical'] else '', 'Evidence items':len(session.core.evidence.get(key,[]))})
        st.dataframe(pd.DataFrame(inv),use_container_width=True,hide_index=True)
        if snap['conflicts']:
            st.error('Conflicting documents: '+', '.join(case.labels[k] for k in snap['conflicts'])+'. Do not assume either source is correct.')
        elif any(len({ev.value for ev in session.core.evidence.get(key,[]) if ev.method!='manual'})>1 for key in case.labels):
            st.warning('Source disagreement remains in the ledger. A manual clarification can unblock the illustrative rule but does not verify which document is correct.')
        st.caption('Unknown ≠ non-compliant. A source-grounded statement ≠ independently verified truth. Manual answers are unverified input.')
        with st.expander('Available source passages and retrieval ranking',expanded=False):
            if session.segments:
                target=st.selectbox('Inspect retrieval for fact',list(case.labels),format_func=lambda x:case.labels[x],key='v2_retrieval_target')
                try:
                    ranks=ranked_segments(case.keywords[target],session.segments,rank_key)
                    st.dataframe(pd.DataFrame([{'Rank':i,'Document':seg.title,'Location':seg.location,'Score':round(score,4),'Inspected':seg.id in session.inspected} for i,(seg,score) in enumerate(ranks[:20],1)]),use_container_width=True,hide_index=True)
                except Exception as exc: st.error(f'Retrieval unavailable: {exc}')
    with colright:
        render_section('Agent next action','The system chooses what to inspect next, or which fact needs clarification.')
        try: action=next_action(session,rank_key)
        except Exception as exc:
            st.error(f'Retrieval could not run: {exc}')
            return
        if action.kind=='stop':
            if snap['status']=='ELIGIBLE': st.success('Decision under the fictional policy: eligible')
            elif snap['status']=='NOT ELIGIBLE': st.error('Decision under the fictional policy: not eligible')
            else: st.warning('Insufficient evidence; no actionable next source identified')
            st.caption(action.reason)
        elif action.kind=='search':
            seg=next(s for s in session.segments if s.id==action.segment_id)
            st.markdown(f'**Inspect:** {escape(seg.title)} · {escape(seg.location)}')
            st.info(action.reason)
            st.caption(f'Heuristic retrieval score: {action.score:.3f} · Expected cost: 1 unit')
            with st.expander('Preview source passage (not yet extracted)',expanded=False):
                st.code(seg.text[:1800],language='text')
        else:
            st.warning('Clarification / manual reconciliation needed')
            st.write(action.reason)
            st.caption('The system will not invent or reveal a hidden supplier answer.')
        if action.kind=='search':
            colstep,colrun=st.columns(2)
            def run_one(act):
                return inspect_segment(session,act.segment_id,'offline' if extraction_mode=='Offline patterns' else 'openai',api_key,llm_model)
            with colstep:
                if st.button('Inspect next passage',type='primary',use_container_width=True):
                    try:
                        claims=run_one(action)
                        st.session_state['v2_last']=claims
                        st.rerun()
                    except Exception as exc: st.error(f'Extraction failed without updating the state: {exc}')
            with colrun:
                if st.button('Run until clarification',use_container_width=True):
                    try:
                        for _ in range(12):
                            act=next_action(session,rank_key)
                            if act.kind!='search': break
                            run_one(act)
                        st.rerun()
                    except Exception as exc: st.error(f'Processing stopped: {exc}')
        elif action.kind=='clarify' and action.fact_key:
            with st.form('v2_manual_answer'):
                st.markdown(f'**{case.labels[action.fact_key]}**')
                answer=st.radio('Manual answer',['Yes','No'],horizontal=True)
                submitted=st.form_submit_button('Record unverified clarification',type='primary')
                if submitted:
                    add_clarification(session,action.fact_key,answer=='Yes')
                    st.rerun()
        if st.button('Reset document analysis',key='v2_reset'):
            st.session_state.pop('v2_signature',None)
            st.rerun()
        if session.inspected:
            st.caption(f'Source passages inspected: {len(session.inspected)} / {len(session.segments)}')
    st.divider()
    render_section('Evidence Ledger','Claims, verbatim passages, locations, methods and unresolved disagreements')
    rows=ledger_rows(session)
    if rows:
        df=pd.DataFrame(rows)
        st.dataframe(df,hide_index=True,use_container_width=True)
        st.download_button('Download evidence ledger CSV',df.to_csv(index=False),'evidencepath_v2_ledger.csv','text/csv')
        for idx,record in enumerate(rows):
            if record['Method'] in ('offline-pattern','llm-extracted / exact-span'):
                with st.expander(f"{record['Fact']} · {record['Value']} · {record['Source']} · {record['Location']}"):
                    st.code(record['Quote'],language='text')
                    st.caption(f"Method: {record['Method']} · Verbatim source grounding: {record['Verbatim grounded']}. This does not prove real-world truth.")
    else:
        st.info('No observed evidence yet. Inspect a passage to populate the ledger.')
    with st.expander('Evidence / policy dependency graph'):
        st.graphviz_chart(to_dot(session.core),use_container_width=True)
    with st.expander('Acquisition trace'):
        if session.events: st.dataframe(pd.DataFrame(session.events),hide_index=True,use_container_width=True)
        else: st.caption('No acquisition steps executed.')
    st.caption('Research prototype only. Do not use to certify supplier compliance, make legal conclusions, or autonomously approve a vendor.')
