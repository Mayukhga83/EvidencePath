"""Repeatable V3 fixture stress test; NOT an independent real-document benchmark.

Creates variants of the three fictional supplier cases by dropping passages,
adding irrelevant documents, and sometimes adding contradicting reports.
All baselines receive identical observations. Supplier answers stay in the
benchmark's oracle only; the evaluation agent never receives them.
"""
from __future__ import annotations
from dataclasses import replace
import argparse
import random
import pandas as pd
from .cases import curated_cases
from .document_lab import Segment, sample_segments, start_session, inspect_segment, next_action, extract_offline
from .logic import decision_snapshot, evaluate
from .models import Document
from .retrieval import bm25_scores


def generate_variants(n: int = 90, seed: int = 23) -> list[tuple[str, list[Segment], dict, str]]:
    rnd = random.Random(seed)
    cases=curated_cases()
    variants=[]
    for i in range(n):
        case=cases[i%len(cases)]
        segs=list(sample_segments(case.id))
        segs=[s for s in segs if rnd.random() >= 0.15]
        if rnd.random()<.55:
            segs.append(Segment(f'noise-{i}',f'noise-{i}', 'Supplier press release',
              'The supplier announced a partnership and published quarterly revenue highlights. '
              'This note does not document security controls, hosting approvals or processing scope.', 'Text'))
        if case.id=='cloud-host' and rnd.random()<.28:
            segs.append(Segment(f'conflict-{i}',f'conflict-{i}', 'Outdated hosting memo',
                'The processing region is not approved for production client records.', 'Text'))
        if case.id=='contradictory-evidence' and rnd.random()<.4:
            segs.append(Segment(f'claim-{i}',f'claim-{i}', 'Vendor sales brochure',
                'Database encryption at rest is enabled.', 'Text'))
        rnd.shuffle(segs)
        variants.append((case.id,segs,dict(case.supplier_answers),f'{case.id}-{i}'))
    return variants


def _execute(case_id: str, segs: list[Segment], strategy: str, budget: int) -> dict:
    session=start_session(case_id,segs)
    if strategy=='adaptive':
        for _ in range(budget):
            action=next_action(session,'hybrid')
            if action.kind!='search': break
            inspect_segment(session,action.segment_id)
    elif strategy in ('static_two','retrieve_first'):
        query=' '.join(session.case.keywords[k] for k in session.case.labels if k in session.case.keywords)
        texts=[s.title+' '+s.text for s in segs]
        scores=bm25_scores(query,texts).tolist() if segs else []
        ranked=sorted(range(len(segs)),key=lambda i:(-scores[i],segs[i].id))
        max_docs=min(2,budget) if strategy=='static_two' else budget
        for ix in ranked[:max_docs]:
            # static RAG retrieves only once; retrieve-first may finish early.
            if strategy=='retrieve_first' and decision_snapshot(session.core)['status']!='UNRESOLVED': break
            inspect_segment(session,segs[ix].id)
    else: raise ValueError(strategy)
    snap=decision_snapshot(session.core)
    return {'decision':snap['status'],'cost':session.cost,'inspections':len(session.inspected),
            'conflict':bool(snap['conflicts']), 'needs_clarification':next_action(session).kind=='clarify'}


def run_stress_benchmark(n: int=90, seed: int=23, budget: int=5) -> tuple[pd.DataFrame,pd.DataFrame]:
    rows=[]
    for case_id,segs,truth,case_label in generate_variants(n,seed):
        case=next(c for c in curated_cases() if c.id==case_id)
        oracle='ELIGIBLE' if evaluate(case.rule,truth) else 'NOT ELIGIBLE'
        for policy in ['static_two','retrieve_first','adaptive']:
            outcome=_execute(case_id,segs,policy,budget)
            decided=outcome['decision']!='UNRESOLVED'
            rows.append({'case_id':case_label,'strategy':policy,'oracle':oracle,**outcome,
                         'decided':int(decided),'correct':int(decided and outcome['decision']==oracle),
                         'incorrect':int(decided and outcome['decision']!=oracle)})
    raw=pd.DataFrame(rows)
    summary=raw.groupby('strategy',sort=False).agg(cases=('case_id','count'),
        coverage=('decided','mean'),correctly_resolved=('correct','mean'),
        incorrect=('incorrect','mean'),mean_passages=('inspections','mean'),
        conflict_flagged=('conflict','mean'),mean_cost=('cost','mean')).reset_index()
    return raw,summary


def main():
    p=argparse.ArgumentParser(description='Run controlled V3 passage-noise benchmark')
    p.add_argument('--n',type=int,default=90)
    p.add_argument('--seed',type=int,default=23)
    p.add_argument('--budget',type=int,default=5)
    p.add_argument('--output',default='results')
    args=p.parse_args()
    from pathlib import Path
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    raw,summary=run_stress_benchmark(args.n,args.seed,args.budget)
    raw.to_csv(out/'v3_stress_raw.csv',index=False)
    summary.to_csv(out/'v3_stress_summary.csv',index=False)
    print(summary.to_string(index=False))

if __name__=='__main__': main()
