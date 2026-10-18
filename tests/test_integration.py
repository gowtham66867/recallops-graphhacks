"""These tests require the REAL FalkorDB service: docker compose up -d."""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from backend.store import Store
from backend.engine import investigate,check_actions,propose,approve,execute,change_state,simulate,Conflict
from backend.agent import run
from backend.main import app

@pytest.fixture
def store_factory():
    prefix='test_'+uuid4().hex
    stores=[]
    def make(scenario='checkout'):
        s=Store(scenario,prefix=prefix);s.seed();stores.append(s);return s
    yield make
    for name in {s.name for s in stores}:
        Store(prefix=prefix).db.select_graph(name).delete()

@pytest.mark.parametrize('scenario,expected',[('checkout','disable_flag'),('rollback-valid','rollback'),('unknown',None),('pool','scale_pool'),('dependency','disable_flag')])
def test_scenario_decisions(store_factory,scenario,expected):
    result=investigate(store_factory(scenario))
    assert (result['recommendation'] or {}).get('action')==expected

def test_graph_relationships_and_evidence(store_factory):
    s=store_factory();r=investigate(s)
    assert {x['service']['id'] for x in r['dependencies']}=={'payments','orders','postgres'}
    assert len(r['history'])==2
    for c in r['checks']:
        for id in c['evidence']: assert s.get(id) is not None
    assert next(c for c in r['checks'] if c['action']=='rollback')['status']=='contradicted'
    assert next(c for c in r['checks'] if c['action']=='restart')['status']=='contradicted'

def test_changed_dependency(store_factory):
    a=store_factory();b=store_factory('dependency')
    assert len(b.dependencies())>len(a.dependencies())
    assert 'inventory' in {x['service']['id'] for x in b.dependencies()}

def test_unknown_not_safe(store_factory):
    r=investigate(store_factory('unknown'))
    assert r['recommendation'] is None
    assert next(c for c in r['checks'] if c['action']=='rollback')['status']=='unknown'

def test_approval_required(store_factory):
    s=store_factory();a=propose(s,'disable_flag','session-1')
    with pytest.raises(Conflict,match='approval'):execute(s,a['id'])
    assert s.get('current')['error_rate']==18.4
    assert s.lessons()==[]

def test_reject_unsupported_proposal(store_factory):
    with pytest.raises(Conflict):propose(store_factory(),'rollback','session')

def test_stale_before_approval(store_factory):
    s=store_factory();a=propose(s,'disable_flag','session');change_state(s)
    with pytest.raises(Conflict,match='State changed'):approve(s,a['id'])
    assert s.get(a['id'])['status']=='invalidated'

def test_stale_after_approval(store_factory):
    s=store_factory();a=propose(s,'disable_flag','session');approve(s,a['id']);change_state(s)
    with pytest.raises(Conflict):execute(s,a['id'])
    assert s.lessons()==[]

def test_execution_idempotence_and_persistence(store_factory):
    s=store_factory();a=propose(s,'disable_flag','session-1');approve(s,a['id'])
    first=execute(s,a['id']);again=execute(s,a['id'])
    assert first==again
    assert first['transitions']==['proposed','approved','executing','succeeded']
    assert s.get('current')['error_rate']==.2
    fresh=Store(s.scenario,prefix=s.name.rsplit('_checkout',1)[0]);fresh.seed()
    assert len(fresh.lessons())==1
    assert fresh.lessons()[0]['signature']=='feature_contract'
    assert fresh.get(fresh.lessons()[0]['source_id'])['kind']=='Source'
    assert investigate(fresh)['recommendation'] is None
    # New interpreter has no application-side memory.
    code='from backend.store import Store; s=Store(prefix='+repr(s.name.rsplit('_checkout',1)[0])+'); print(len(s.lessons()))'
    assert subprocess.check_output([sys.executable,'-c',code],text=True).strip()=='1'

def test_concurrent_execution_only_one_outcome(store_factory):
    s=store_factory();a=propose(s,'disable_flag','session');approve(s,a['id'])
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:execute(s,a['id']),range(4)))
    assert all(r['status']=='succeeded' for r in results)
    assert len(s.lessons())==1
    assert s.get('current')['revision']==2

def test_proposal_not_outcome(store_factory):
    s=store_factory();a=propose(s,'disable_flag','session')
    assert a['status']=='proposed' and len(s.lessons())==0
    assert s.query('MATCH (a:Entity {id:$id})-[:RESULTED_IN]->(o) RETURN o.id',{'id':a['id']})==[]

def test_simulator_does_not_fake_recovery():
    i={'signature':'pool_exhaustion','flag_enabled':True,'pool_saturated':True,'error_rate':22.1,'status':'investigating','revision':1}
    updated,status=simulate(i,'disable_flag')
    assert updated['error_rate']==22.1 and status=='failed'
    assert i['flag_enabled'] is True

def test_seed_is_idempotent(store_factory):
    s=store_factory();before=s.snapshot();s.seed();after=s.snapshot()
    assert len(before['nodes'])==len(after['nodes'])
    assert len(before['edges'])==len(after['edges'])

def test_database_failure_visible(monkeypatch):
    monkeypatch.setenv('FALKORDB_PORT','6398')
    response=TestClient(app).get('/api/health')
    assert response.status_code==503
    assert 'No fallback' in response.json()['detail']

def test_api_flow_and_validation(monkeypatch):
    prefix='api_'+uuid4().hex;monkeypatch.setenv('FALKORDB_GRAPH',prefix)
    c=TestClient(app)
    try:
        assert c.get('/api/no-scenario/snapshot').status_code==404
        session=c.post('/api/checkout/session',json={}).json()['session_id']
        assert c.post('/api/checkout/proposals',json={'action':'disable_flag','session_id':'bad'}).status_code==422
        investigation=c.post('/api/checkout/investigate',json={})
        assert investigation.status_code==200
        run_id=investigation.json()['run_id']
        a=c.post('/api/checkout/proposals',json={'action':'disable_flag','session_id':session,'run_id':run_id}).json()
        assert c.post('/api/checkout/proposals/'+a['id']+'/execute',json={}).status_code==409
        assert c.post('/api/checkout/proposals/'+a['id']+'/approve',json={}).status_code==200
        assert c.post('/api/checkout/proposals/'+a['id']+'/execute',json={}).json()['status']=='succeeded'
        assert len(c.post('/api/checkout/session',json={}).json()['lessons'])==1
        assert c.post('/api/checkout/reset',json={},headers={'Origin':'https://untrusted.example'}).status_code==403
        assert c.get('/api/checkout/evidence/missing').status_code==404
    finally:Store(prefix=prefix).graph.delete()

def test_live_key_missing_is_explicit(store_factory,monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with pytest.raises(ValueError,match='OPENAI_API_KEY'):run(store_factory(),'Investigate',True)

def test_live_adapter_tool_roundtrip(store_factory):
    # Contract test only; intentionally does not pretend a mocked API is a live model.
    names=['get_current_incident','inspect_service_dependencies','find_related_incidents','check_action_preconditions','recall_lessons','simulate_counterfactual','submit_assessment']
    requests=[]
    def create(**kwargs):
        requests.append(kwargs)
        n=len(requests)-1
        if n<len(names):
            arguments='{}' if names[n]!='submit_assessment' else __import__('json').dumps({'recommended_action':'disable_flag','explanation':'Disable the compatible feature path; rollback contradicts the current schema.','source_ids':['src-deploy','src-alert'],'uncertainties':['Synthetic telemetry only.']})
            return SimpleNamespace(output=[SimpleNamespace(type='function_call',name=names[n],arguments=arguments,call_id=str(n))])
        return SimpleNamespace(output=[],output_text='Schema v3 contradicts the previous rollback [src-deploy].')
    client=SimpleNamespace(responses=SimpleNamespace(create=create))
    result=run(store_factory(),'Investigate',True,client=client)
    assert result['mode']=='live' and len(result['trace'])==7
    assert any(isinstance(i,dict) and i.get('type')=='function_call_output' for i in requests[-1]['input'])
    assert result['recommendation']['action']=='disable_flag'

def test_recurrence_uses_conditional_memory(store_factory):
    from backend.engine import recur
    s=store_factory();a=propose(s,'disable_flag','one');approve(s,a['id']);execute(s,a['id'])
    recur(s)
    result=investigate(s)
    assert result['recommendation']['recalled_lesson_ids']==[s.lessons()[0]['id']]
    assert s.lessons()[0]['source_id'] in result['recommendation']['evidence']
    # Old lesson remains in history, but does not match a changed schema.
    m=s.get('migration');m['schema']=4;s.put(m)
    assert investigate(s)['recommendation'] is None
    assert next(c for c in check_actions(s) if c['action']=='disable_flag')['recalled_lesson_ids']==[]
    assert len(s.lessons())==1

def test_rollback_updates_deployment(store_factory):
    s=store_factory('rollback-valid');a=propose(s,'rollback','one');approve(s,a['id']);execute(s,a['id'])
    assert s.get('deploy-current')['version']=='v2.7.0'
