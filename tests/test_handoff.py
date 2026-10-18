from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from backend.store import Store
from backend.main import app
from backend.handoff import ReportInput,add_report,reports,redact_report,create_packet,approve_packet,export_packet,redact
from backend.engine import check_actions,Conflict,propose
from backend.workflow import run_workflow
from backend.evidence import current_digest
from backend.agent import tool_value

@pytest.fixture
def store():
    s=Store(prefix='context_test_'+uuid4().hex);s.seed();yield s;s.graph.delete()


def test_reports_preserve_exact_masked_quotes_without_promoting_observation(store):
    before=check_actions(store)
    note=add_report(store,ReportInput(text='Restart worked, password=supersecret user@example.com',category='prior_attempt',outcome='reported_resolved'))
    assert 'supersecret' not in note['text'] and 'user@example.com' not in note['text']
    assert note['quote']==store.get(note['source_id'])['text']
    assert note['verified'] is False and note['classification']=='operator_report'
    assert check_actions(store)==before
    assert store.lessons()==[] and store.get('current')['error_rate']==18.4
    assert tool_value(store,'get_current_incident')['operator_reports'][0]['id']==note['id']


def test_correction_retains_prior_source_and_invalidates_investigation(store):
    n=add_report(store,ReportInput(text='Restart seemed to help.'))
    run=run_workflow(store,'Check current context')
    c=add_report(store,ReportInput(text='Correction: errors persisted after restart.',category='correction',supersedes=n['id']))
    assert store.get(n['id'])['active'] is False
    assert store.get(n['source_id'])['text']=='Restart seemed to help.'
    assert c['supersedes']==n['id']
    with pytest.raises(Conflict,match='stale'):propose(store,'disable_flag',str(uuid4()),run['run_id'])
    with pytest.raises(Conflict):add_report(store,ReportInput(text='Again',category='correction',supersedes=n['id']))


def test_human_review_is_available_without_completed_workflow(store):
    p=create_packet(store)
    assert p['human_review_requested'] and p['internal']['ticket_sent'] is False
    assert p['internal']['sources'] and p['internal']['prior_attempts']
    assert p['internal']['unknowns']
    assert all(s['synthetic'] for s in p['internal']['sources'])


@pytest.mark.parametrize('audience',['internal','anonymized'])
def test_export_needs_exact_audience_approval_and_current_digest(store,audience):
    p=create_packet(store)
    with pytest.raises(Conflict,match='approval'):export_packet(store,p['id'],audience)
    approve_packet(store,p['id'],audience)
    assert export_packet(store,p['id'],audience)==p[audience]
    other='anonymized' if audience=='internal' else 'internal'
    with pytest.raises(Conflict):export_packet(store,p['id'],other)
    add_report(store,ReportInput(text='New context'))
    with pytest.raises(Conflict,match='changed'):export_packet(store,p['id'],audience)
    with pytest.raises(Conflict,match='changed'):approve_packet(store,p['id'],audience)


def test_anonymized_packet_omits_reports_identifiers_quotes_and_precise_metrics(store):
    import json
    add_report(store,ReportInput(text='Alice reported payment value 2400; host private-db-17.'))
    p=create_packet(store);approve_packet(store,p['id'],'anonymized')
    result=json.dumps(export_packet(store,p['id'],'anonymized'))
    for value in ['Alice','2400','private-db-17','18.4','INC-024','src-alert','report-']:assert value not in result


def test_redaction_removes_retained_run_and_packet_copies(store):
    n=add_report(store,ReportInput(text='Sensitive detail to remove'))
    run=run_workflow(store,'Read reports');p=create_packet(store);approve_packet(store,p['id'],'internal')
    before=current_digest(store)
    redact_report(store,n['id'])
    assert current_digest(store)!=before
    assert store.get(n['id'])['text']=='[operator redacted]'
    assert store.get(n['source_id'])['text']=='[operator redacted]'
    assert store.get(run['run_id']) is None and store.get(p['id']) is None
    assert not store.query('MATCH (n:Entity) WHERE n.kind=$kind RETURN n.id',{'kind':'Checkpoint'})
    with pytest.raises(Conflict):export_packet(store,p['id'],'internal')


def test_redaction_waits_out_active_privacy_lease(store):
    n=add_report(store,ReportInput(text='Retained report'))
    from redis.exceptions import LockError
    with store.db.connection.lock(store.name+':privacy',timeout=20,blocking_timeout=1):
        with pytest.raises(LockError):redact_report(store,n['id'])
    assert store.get(n['id'])['text']=='Retained report'


def test_report_limit_does_not_drop_old_context(store):
    for i in range(40):add_report(store,ReportInput(text=f'Observation {i}'))
    with pytest.raises(Conflict,match='40-report'):add_report(store,ReportInput(text='Overflow'))
    assert len(reports(store))==40


def test_handoff_api_rejects_invalid_audiences_and_stale_exports(monkeypatch):
    monkeypatch.setenv('FALKORDB_GRAPH','handoff_api_'+uuid4().hex)
    s=Store();c=TestClient(app)
    try:
        p=c.post('/api/checkout/handoff').json()
        assert c.post(f'/api/checkout/handoff/{p["id"]}/approve',json={'audience':'everyone'}).status_code==422
        assert c.post(f'/api/checkout/handoff/{p["id"]}/export',json={'audience':'internal'}).status_code==409
        assert c.post(f'/api/checkout/handoff/{p["id"]}/approve',json={'audience':'internal'}).status_code==200
        assert c.post('/api/checkout/reports',json={'text':'New unknown','category':'gap'}).status_code==200
        assert c.post(f'/api/checkout/handoff/{p["id"]}/export',json={'audience':'internal'}).status_code==409
    finally:s.graph.delete()


@pytest.mark.parametrize('text',['Bearer abc.secret.token','api_key=hidden_value','sk-abcdefghijklmnopqrstuvwxyz12345','ghp_abcdefghijklmnopqrstuvwxyz','owner@example.com'])
def test_common_secrets_are_masked(text):assert redact(text)!=text
