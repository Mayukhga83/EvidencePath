from evidencepath.document_lab import (
    start_session, next_action, inspect_segment, uploaded_segments, extract_offline,
    Segment, add_clarification, ledger_rows
)
from evidencepath.logic import decision_snapshot


def test_document_lab_does_not_expose_hidden_oracles():
    s=start_session('cloud-host')
    assert s.core.case.supplier_answers == {}
    assert s.core.case.documents == ()
    assert s.core.case.preloaded_documents == ()
    assert 'hosting' not in decision_snapshot(s.core)['known']
    a=next_action(s)
    assert a.kind=='search'
    extracted=inspect_segment(s,a.segment_id)
    assert any(c.key=='hosting' and c.value for c in extracted)
    assert decision_snapshot(s.core)['status']=='ELIGIBLE'
    assert all(r['Quote'] and r['Source'] for r in ledger_rows(s))


def test_exemption_needs_no_acquisition():
    s=start_session('sandbox-exemption')
    assert next_action(s).kind == 'stop'
    assert decision_snapshot(s.core)['status']=='ELIGIBLE'
    assert s.cost==0


def test_conflicting_sources_requires_manual_resolution():
    s=start_session('contradictory-evidence')
    first=next_action(s)
    assert first.kind=='search'
    inspect_segment(s,first.segment_id)
    second=next_action(s)
    assert second.kind=='search' and second.segment_id!=first.segment_id
    inspect_segment(s,second.segment_id)
    assert 'encryption' in decision_snapshot(s.core)['conflicts']
    assert next_action(s).kind=='clarify'
    add_clarification(s,'encryption',False)
    assert decision_snapshot(s.core)['status']=='NOT ELIGIBLE'
    assert any(not r['Verbatim grounded'] for r in ledger_rows(s) if r['Method']=='manual')


def test_negative_statement_beats_positive_token():
    seg=Segment('1','1','Audit','Production database encryption at rest is not enabled in the legacy cluster.','Page 4')
    result=extract_offline(seg,['encryption'])
    assert len(result)==1 and result[0].value is False
    assert 'not enabled' in result[0].quote


def test_no_hallucinated_assertion_on_irrelevant_input():
    seg=Segment('1','1','Irrelevant','Our annual staff picnic was held on Friday.','Text')
    assert extract_offline(seg,['encryption','hosting','review'])==[]


def test_upload_utf8_text_and_source():
    segs=uploaded_segments('note.txt','Hosting region is approved.\n\nEncryption at rest is enabled.'.encode(),'UP1')
    assert len(segs)==2
    assert all(s.title=='note.txt' and s.location=='Text' for s in segs)
    assert {e.key for seg in segs for e in extract_offline(seg,['hosting','encryption'])}=={'hosting','encryption'}


def test_invalid_extension_and_oversized_upload():
    from pytest import raises
    with raises(ValueError): uploaded_segments('archive.exe',b'hi','X')
    with raises(ValueError): uploaded_segments('note.txt',b'a'*(8*1024*1024+1),'X')


def test_source_conflict_from_uploaded_text_only():
    from evidencepath.document_lab import _parts_to_segments
    segs = (_parts_to_segments('A','Vendor claim',[('Text','Database encryption at rest is enabled.')])+
            _parts_to_segments('B','Audit observation',[('Text','Database encryption at rest is not enabled.')]))
    s=start_session('contradictory-evidence',segs)
    for seg in segs:
        inspect_segment(s,seg.id)
    snap=decision_snapshot(s.core)
    assert 'encryption' in snap['conflicts']
    assert snap['status']=='UNRESOLVED'


def test_pdf_parsing_captures_actual_page_number():
    pytest = __import__('pytest')
    pytest.importorskip('pypdf')
    reportlab=pytest.importorskip('reportlab')
    from io import BytesIO
    from reportlab.pdfgen import canvas
    buf=BytesIO()
    c=canvas.Canvas(buf)
    c.drawString(60,700,'Hosting region is approved.')
    c.showPage()
    c.save()
    segs=uploaded_segments('supplier.pdf',buf.getvalue(),'PDF1')
    assert segs and segs[0].location=='Page 1'
    assert 'Hosting region is approved' in segs[0].text
    assert any(f.key=='hosting' and f.value for seg in segs for f in extract_offline(seg,['hosting']))
