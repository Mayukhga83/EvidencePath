"""Pure-core tests for V3's counterfactuals, reports, limits and text benchmarks."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from evidencepath.cases import curated_cases
from evidencepath.document_lab import start_session, next_action, inspect_segment
from evidencepath.counterfactual import alternatives
from evidencepath.reporting import report_markdown, report_json
from evidencepath.runtime import server_key, reserve_live_call
from evidencepath.stress_benchmark import run_stress_benchmark, generate_variants


def test_counterfactual_material_unknown():
    case=start_session('cloud-host')
    result=alternatives(case.core,'hosting')
    assert result['current']=='UNKNOWN'
    assert result['if_yes']=='ELIGIBLE'
    assert result['if_no']=='NOT ELIGIBLE'
    assert result['changes_decision']


def test_counterfactual_irrelevant_unknown():
    case=start_session('cloud-host')
    result=alternatives(case.core,'revenue')
    assert not result['in_rule']
    assert not result['changes_decision']
    assert result['if_yes']==result['if_no']=='UNRESOLVED'


def test_session_report_contains_observed_quote_not_hidden_answer():
    case=start_session('cloud-host')
    action=next_action(case)
    assert action.kind=='search'
    claims=inspect_segment(case,action.segment_id)
    assert claims
    raw=report_json(case)
    loaded=json.loads(raw)
    assert loaded['evidence_ledger']
    assert loaded['policy_type'].startswith('Fictional')
    assert loaded['inspected_passages']==1
    md=report_markdown(case).decode()
    for ev in loaded['evidence_ledger']:
        if ev['Method']=='offline-pattern':
            assert ev['Quote'] in md
    assert 'not independently verified' in md.lower() or 'not a legal' in md.lower()


def test_no_browser_key_and_file_secrets_override(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    assert server_key({})==''
    assert server_key({'OPENAI_API_KEY':'test-server-key'})=='test-server-key'
    monkeypatch.setenv('OPENAI_API_KEY','env-server-key')
    assert server_key({'OPENAI_API_KEY':'other'})=='env-server-key'


def test_best_effort_process_quota_atomic(tmp_path):
    db=tmp_path/'demo.sqlite3'
    c=reserve_live_call(0,db_path=db,daily_cap=2)
    assert c==1
    c=reserve_live_call(c,db_path=db,daily_cap=2)
    assert c==2
    with pytest.raises(RuntimeError,match='daily demo budget'):
        reserve_live_call(c,db_path=db,daily_cap=2)


def test_generated_variants_stable():
    first=generate_variants(15,23)
    second=generate_variants(15,23)
    assert first==second
    assert len(first)==15
    raw,summary=run_stress_benchmark(12,seed=23,budget=4)
    assert len(raw)==36
    assert set(summary['strategy'])=={'static_two','retrieve_first','adaptive'}
    assert all(raw['inspections']<=4)
    assert all(raw['incorrect']<=raw['decided'])


def test_llm_schema_output_discards_nonverbatim_quotes(monkeypatch):
    """Fake the SDK; tests source grounding without making paid API calls."""
    import sys
    from types import SimpleNamespace
    from evidencepath.document_lab import Segment, extract_openai
    class FakeResponse:
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=SimpleNamespace(claims=[
            SimpleNamespace(key='encryption',value=True,quote='Encryption at rest is enabled.'),
            SimpleNamespace(key='review',value=True,quote='This quote is fabricated and does not exist.'),
            SimpleNamespace(key='not_in_labels',value=True,quote='Encryption at rest is enabled.'),
        ])))]
    class MockOpenAI:
        def __init__(self,**kwargs):
            assert kwargs['api_key']=='server-only-test-key'
            self.beta=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=lambda **kw:FakeResponse())))
    monkeypatch.setitem(sys.modules,'openai',SimpleNamespace(OpenAI=MockOpenAI))
    seg=Segment('S','D','Audit','Encryption at rest is enabled.','Page 2')
    result=extract_openai(seg,{'encryption':'encryption enabled','review':'review complete'},'server-only-test-key')
    assert len(result)==1
    assert result[0].key=='encryption'
    assert result[0].quote in seg.text
    assert result[0].method=='llm-structured / exact-span'
