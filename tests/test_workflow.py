"""Durable workflow and adversarial evidence tests against real FalkorDB."""
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from backend.store import Store
from backend.workflow import run_workflow,validate_handoff,CriticVerdict
from backend.evidence import current_digest,citation_check,counterfactuals
from backend.engine import check_actions,propose,approve,execute,Conflict
from backend.main import app

@pytest.fixture
def store():
    s=Store(prefix='workflow_'+uuid4().hex);s.seed()
    yield s
    s.graph.delete()


def test_durable_run_and_verified_handoff(store):
    r=run_workflow(store,'What changed?')
    saved=store.get(r['run_id'])
    assert saved['status']=='completed'
    assert set(saved['checkpoints'])=={'plan','collect','reason','review','complete'}
    assert r['verification']['status']=='passed'
    assert len(r['specialists'])==3
    assert all(s['kind']=='deterministic specialist' for s in r['specialists'])
    assert len(store.query('MATCH (r:Entity {id:$id})-[:CHECKPOINTED]->(c) RETURN c.id',{'id':r['run_id']}))==5
    assert validate_handoff(store,r['run_id'],'disable_flag')['id']==r['run_id']


def test_counterfactuals_are_predictions_and_non_mutating(store):
    before=current_digest(store)
    rows=counterfactuals(store,check_actions(store))
    assert current_digest(store)==before
    assert all(r['observed'] is False and r['classification']=='prediction' for r in rows)
    assert next(r for r in rows if r['action']=='disable_flag')['predicted_error_rate']==.2
    assert next(r for r in rows if r['action']=='rollback')['verdict']=='blocked'
    assert next(r for r in rows if r['action']=='rollback')['predicted_error_rate'] is None
    assert store.lessons()==[]


def test_stale_handoff_detects_schema_changes_without_revision(store):
    r=run_workflow(store,'Investigate')
    migration=store.get('migration');migration['schema']=2;store.put(migration)
    with pytest.raises(Conflict,match='stale'):validate_handoff(store,r['run_id'],'disable_flag')


def test_changed_original_source_invalidates_approval(store):
    r=run_workflow(store,'Investigate');a=propose(store,'disable_flag','one',r['run_id'])
    source=store.get('src-deploy');source['text']='Corrected synthetic manifest';store.put(source)
    with pytest.raises(Conflict,match='State changed'):approve(store,a['id'])


def test_wrong_action_cannot_use_verified_run(store):
    r=run_workflow(store,'Investigate')
    with pytest.raises(Conflict,match='verified recommendation'):validate_handoff(store,r['run_id'],'rollback')


def test_new_session_does_not_invalidate_evidence(store):
    r=run_workflow(store,'Investigate')
    store.put({'id':'session-new','kind':'Session','title':'Fresh session'})
    assert current_digest(store)==r['state_hash']
    assert validate_handoff(store,r['run_id'],'disable_flag')


def test_citations_reject_invented_ids_and_non_sources(store):
    facts=store.fact_snapshot()
    assert citation_check('Current schema [src-deploy]',facts)['passed']
    assert not citation_check('Invented evidence [src-not-real]',facts)['passed']
    assert not citation_check('A service is not an original source [checkout]',facts)['passed']
    assert not citation_check('No references.',facts)['passed']


def test_resume_skips_completed_specialists_after_failure(store,monkeypatch):
    import backend.workflow as wf
    original=wf.researcher
    def fail(*args,**kwargs):raise RuntimeError('simulated process boundary')
    monkeypatch.setattr(wf,'researcher',fail)
    with pytest.raises(RuntimeError):run_workflow(store,'Investigate')
    run_id=store.query('MATCH (r:Entity) WHERE r.kind=$kind RETURN r.id',{'kind':'InvestigationRun'})[0][0]
    interrupted=store.get(run_id)
    assert interrupted['status']=='interrupted'
    assert set(interrupted['checkpoints'])=={'plan','collect'}
    monkeypatch.setattr(wf,'researcher',original)
    def do_not_recollect(*args):raise AssertionError('Completed collection must not run again')
    monkeypatch.setattr(wf,'collect',do_not_recollect)
    resumed=run_workflow(store,'ignored new prompt',run_id=run_id)
    assert resumed['workflow']['resume_count']==1
    assert resumed['recommendation']['action']=='disable_flag'


def test_resume_refuses_changed_evidence(store,monkeypatch):
    import backend.workflow as wf
    def fail(*args,**kwargs):raise RuntimeError('stop')
    monkeypatch.setattr(wf,'researcher',fail)
    with pytest.raises(RuntimeError):run_workflow(store,'Investigate')
    run_id=store.query('MATCH (r:Entity) WHERE r.kind=$kind RETURN r.id',{'kind':'InvestigationRun'})[0][0]
    i=store.get('current');i['flag_enabled']=False;store.put(i)
    with pytest.raises(Conflict,match='Evidence changed'):run_workflow(store,'Investigate',run_id=run_id)


def test_completed_resume_is_idempotent(store):
    r=run_workflow(store,'Investigate')
    assert run_workflow(store,'ignored',run_id=r['run_id'])==r


def test_parallel_invocations_preserve_separate_audits(store):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:run_workflow(store,'Investigate'),range(2)))
    assert len({r['run_id'] for r in results})==2
    assert all(r['verification']['status']=='passed' for r in results)


def test_missing_source_blocks_handoff(store):
    store.query('MATCH (s:Entity {id:$id}) DETACH DELETE s',{'id':'src-alert'})
    r=run_workflow(store,'Investigate')
    assert r['verification']['status']=='blocked' and r['recommendation'] is None
    with pytest.raises(Conflict):validate_handoff(store,r['run_id'],'disable_flag')


def test_live_independent_critic_can_reject(store,monkeypatch):
    import backend.workflow as wf
    from backend.agent import run
    def draft(s,q,live=False,client=None,briefing=None):
        return {**run(s,q,False),'mode':'live','summary':'Rollback is always safe [src-deploy].'}
    monkeypatch.setattr(wf,'researcher',draft)
    calls=[]
    def parse(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_parsed=CriticVerdict(accepted=False,issues=['Rollback claim contradicts schema evidence.'],explanation='Reject the unsupported explanation.'))
    client=SimpleNamespace(responses=SimpleNamespace(parse=parse))
    r=run_workflow(store,'Investigate',True,client=client)
    assert len(calls)==1 and calls[0]['store'] is False
    assert r['critic']['kind']=='independent model critic'
    assert r['verification']['status']=='blocked' and r['recommendation'] is None


def test_bad_citation_blocked_before_model_critic(store,monkeypatch):
    import backend.workflow as wf
    from backend.agent import run
    def draft(s,q,live=False,client=None,briefing=None):
        return {**run(s,q,False),'mode':'live','summary':'Fixed [invented-id].'}
    monkeypatch.setattr(wf,'researcher',draft)
    r=run_workflow(store,'Investigate',True,client=object())
    assert r['critic']['kind']=='citation verifier'
    assert r['verification']['status']=='blocked'


def test_api_requires_verified_run_and_exposes_checkpoint(monkeypatch):
    prefix='workflow_api_'+uuid4().hex;monkeypatch.setenv('FALKORDB_GRAPH',prefix)
    c=TestClient(app)
    try:
        session=c.post('/api/checkout/session',json={}).json()['session_id']
        assert c.post('/api/checkout/proposals',json={'action':'disable_flag','session_id':session}).status_code==422
        r=c.post('/api/checkout/investigate',json={}).json()
        checkpoint=c.get('/api/checkout/runs/'+r['run_id'])
        assert checkpoint.status_code==200 and checkpoint.json()['status']=='completed'
        assert c.post('/api/checkout/runs/'+r['run_id']+'/resume',json={}).json()['run_id']==r['run_id']
        a=c.post('/api/checkout/proposals',json={'action':'disable_flag','session_id':session,'run_id':r['run_id']})
        assert a.status_code==200
    finally:Store(prefix=prefix).graph.delete()

def test_memory_ablation_changes_rollback_decision():
    s=Store('rollback-valid',prefix='ablation_'+uuid4().hex);s.seed()
    try:
        assert next(c for c in check_actions(s) if c['action']=='rollback')['status']=='supported'
        s.query('MATCH (i:Entity)-[r:AFFECTS]->(:Entity {id:$service}) WHERE i.id <> $current DELETE r',{'service':'checkout','current':'current'})
        c=next(c for c in check_actions(s) if c['action']=='rollback')
        assert c['status']=='unknown'
        assert 'src-021' not in c['evidence']
    finally:s.graph.delete()


def test_restart_reason_uses_actual_historical_identity(store):
    incident=store.get('inc-017');incident['code']='INC-900';store.put(incident)
    c=next(c for c in check_actions(store) if c['action']=='restart')
    assert 'INC-900' in c['reason'] and 'INC-017' not in c['reason']

def test_live_submission_selects_supported_action_and_exposes_uncertainty(store):
    import json
    from backend.agent import run,TOOL_NAMES
    tools=list(TOOL_NAMES)
    calls=[]
    def create(**kwargs):
        calls.append(kwargs);idx=len(calls)-1
        if idx<len(tools):name,args=tools[idx],{}
        else:name,args='submit_assessment',{'recommended_action':None,'explanation':'Abstain pending additional telemetry despite an available supported simulator action.','source_ids':['src-alert'],'uncertainties':['The simulator is synthetic.']}
        return SimpleNamespace(output=[SimpleNamespace(type='function_call',name=name,arguments=json.dumps(args),call_id=str(idx))])
    r=run(store,'Investigate conservatively',True,client=SimpleNamespace(responses=SimpleNamespace(create=create)))
    assert r['recommendation'] is None
    assert r['assessment']['uncertainties']==['The simulator is synthetic.']
    assert r['model_usage']['requests']==7
    assert store.lessons()==[]


def test_live_submission_rejects_unsupported_action_before_review(store):
    import json
    from backend.agent import run,TOOL_NAMES
    tools=list(TOOL_NAMES);calls=[]
    def create(**kwargs):
        calls.append(kwargs);idx=len(calls)-1
        if idx<len(tools):name,args=tools[idx],{}
        else:
            name='submit_assessment';args={'recommended_action':'rollback' if idx==len(tools) else 'disable_flag','explanation':'Use only an action with satisfied deterministic preconditions.','source_ids':['src-deploy'],'uncertainties':[]}
        return SimpleNamespace(output=[SimpleNamespace(type='function_call',name=name,arguments=json.dumps(args),call_id=str(idx))])
    r=run(store,'Investigate',True,client=SimpleNamespace(responses=SimpleNamespace(create=create)))
    assert r['recommendation']['action']=='disable_flag'
    assert r['model_usage']['requests']==8
    assert any(isinstance(item,dict) and item.get('type')=='function_call_output' and 'not supported' in item.get('output','') for item in calls[-1]['input'])

def test_observed_state_has_new_provenance_after_action():
    s=Store('rollback-valid',prefix='provenance_'+uuid4().hex);s.seed()
    try:
        r=run_workflow(s,'Investigate');a=propose(s,'rollback','session',r['run_id']);approve(s,a['id']);execute(s,a['id'])
        sources=s.sources_for('deploy-current')
        observed=[source for source in sources if source.get('observed_state',{}).get('deployment')=='v2.7.0']
        assert len(observed)==1
        assert observed[0]['id'] in {source['id'] for source in s.sources_for('current')}
        from backend.agent import tool_value
        assert observed[0]['id'] in {source['id'] for source in tool_value(s,'get_current_incident')['sources']}
    finally:s.graph.delete()

def test_interrupted_run_is_discoverable_in_public_history(monkeypatch):
    import backend.workflow as wf
    prefix='history_api_'+uuid4().hex;monkeypatch.setenv('FALKORDB_GRAPH',prefix)
    def fail(*args,**kwargs):raise RuntimeError('interrupted worker')
    monkeypatch.setattr(wf,'researcher',fail)
    c=TestClient(app)
    try:
        assert c.post('/api/checkout/investigate',json={}).status_code==502
        runs=c.get('/api/checkout/runs').json()
        assert len(runs)==1 and runs[0]['status']=='interrupted'
        assert runs[0]['phase']=='collect'
        assert c.get('/api/checkout/runs/'+runs[0]['id']).status_code==200
    finally:Store(prefix=prefix).graph.delete()
