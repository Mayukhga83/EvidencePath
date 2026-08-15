"""Tiny smoke evaluation of the *bundled examples only*.

The oracle labels here exist solely to test pattern extraction against the
handwritten demo text; document_lab never sees them. Do NOT extrapolate to
real PDFs or unseen supplier documents.
"""
from __future__ import annotations
from .cases import curated_cases
from .document_lab import Segment, extract_offline, start_session, next_action, inspect_segment
from .logic import decision_snapshot


def evaluate_examples() -> dict:
    true_positive=false_positive=missed=0
    for case in curated_cases():
        for doc in case.documents:
            segment=Segment(doc.id,doc.id,doc.title,doc.text,'Bundled example')
            predicted={(x.key,x.value) for x in extract_offline(segment,list(case.labels))}
            gold=set(doc.assertions.items())  # isolated evaluation oracle
            true_positive+=len(predicted & gold)
            false_positive+=len(predicted-gold)
            missed+=len(gold-predicted)
    outcomes=[]
    for case in curated_cases():
        session=start_session(case.id)
        for _ in range(15):
            action=next_action(session)
            if action.kind != 'search': break
            inspect_segment(session,action.segment_id)
        final=next_action(session)
        outcomes.append({'case':case.id,'verdict':decision_snapshot(session.core)['status'],
                         'next_action':final.kind,'inspected_passages':len(session.inspected)})
    return {'fixture_claims_exactly_matched':true_positive,
            'fixture_false_positive_assertions':false_positive,
            'fixture_missing_assertions':missed,
            'cases':outcomes,
            'warning':'Only 10 hand-authored bundled documents. This is an integration smoke test, NOT a generalisation benchmark.'}

if __name__=='__main__':
    import json
    print(json.dumps(evaluate_examples(),indent=2))
