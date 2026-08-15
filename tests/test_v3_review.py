"""Regression tests: source audit remains available after automatic stopping."""
import pytest
from evidencepath.document_lab import (
    start_session, next_action, inspect_segment,
    remaining_passages, manual_review_action, Segment,
)
from evidencepath.logic import decision_snapshot


def test_manual_review_after_automatic_stop_can_change_outcome():
    s = start_session('sandbox-exemption', [
        Segment('LATE', 'SOURCE2', 'Deployment finding',
                'Production integration is enabled for this supplier.', 'Page 4')
    ])
    assert next_action(s).kind == 'stop'  # initial sandbox exemption
    assert decision_snapshot(s.core)['status'] == 'ELIGIBLE'
    assert len(remaining_passages(s)) == 1
    action = manual_review_action(s, 'LATE')
    assert action.kind == 'search'
    claims = inspect_segment(s, action.segment_id)
    assert len(claims) == 1 and claims[0].key == 'sandbox' and claims[0].value is False
    snap = decision_snapshot(s.core)
    assert 'sandbox' in snap['conflicts']
    assert snap['status'] == 'UNRESOLVED'
    assert not remaining_passages(s)
    with pytest.raises(ValueError,match='not available'):
        manual_review_action(s,'LATE')


def test_manual_review_preserves_no_extra_calls_if_no_pending_sources():
    s = start_session('sandbox-exemption', [])
    assert next_action(s).kind == 'stop'
    assert remaining_passages(s) == []
    assert s.cost == 0


def test_reviewing_distractor_does_not_undo_current_decision():
    s = start_session('sandbox-exemption', [
        Segment('UNRELATED','PROFILE','Profile',
                'The company employs 180 people worldwide.', 'Text')
    ])
    assert decision_snapshot(s.core)['status'] == 'ELIGIBLE'
    act = manual_review_action(s,'UNRELATED')
    inspect_segment(s,act.segment_id)
    assert decision_snapshot(s.core)['status'] == 'ELIGIBLE'
    assert s.events[0]['Evidence'] == 1  # an irrelevant policy condition
