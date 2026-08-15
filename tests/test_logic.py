from evidencepath.models import fact,AND,OR,NOT,new_state
from evidencepath.cases import curated_cases
from evidencepath.logic import status, critical_facts,decision_snapshot
from evidencepath.agent import recommend_action,execute_action,run_case


def test_evidence_sufficiency_with_irrelevant_missing_fact():
    policy=OR(fact('exempt'),AND(fact('security'),fact('hosting')))
    assert status(policy,{'exempt':True})=='ELIGIBLE'
    assert critical_facts(policy,{'exempt':True})==[]
    assert status(policy,{'exempt':False,'security':True})=='UNRESOLVED'
    assert critical_facts(policy,{'exempt':False,'security':True})==['hosting']


def test_cloud_can_retrieve_and_decide():
    case=curated_cases()[0]
    state=new_state(case)
    act=recommend_action(state)
    assert act.kind=='retrieve'
    assert act.target=='hosting'
    execute_action(state,act)
    assert decision_snapshot(state)['status']=='ELIGIBLE'
    assert state.searches==1


def test_exemption_stops_without_any_actions():
    state=new_state(curated_cases()[1])
    assert decision_snapshot(state)['status']=='ELIGIBLE'
    assert recommend_action(state).kind=='stop'


def test_conflicting_evidence_requires_clarification():
    state=new_state(curated_cases()[2])
    assert 'encryption' in decision_snapshot(state)['conflicts']
    assert decision_snapshot(state)['status']=='UNRESOLVED'
    act=recommend_action(state)
    assert act.kind=='ask' and act.target=='encryption'
    execute_action(state,act)
    assert decision_snapshot(state)['status']=='NOT ELIGIBLE'
    assert state.questions==1


def test_all_curated_cases_reach_outcome():
    for case in curated_cases():
        state=run_case(new_state(case))
        assert decision_snapshot(state)['status']!='UNRESOLVED'
