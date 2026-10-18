"""Proof Lab exercises real graph storage, workflow handoff, and action authority."""
from uuid import uuid4
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from backend.main import app
from backend.lab import Configuration, lab_store, configure, snapshot
from backend.evidence import current_digest
from backend.workflow import run_workflow
from backend.engine import propose, approve, execute, Conflict

@pytest.fixture
def lab():
    s=lab_store(uuid4())
    yield s
    s.graph.delete()

@pytest.mark.parametrize('config,action',[
    ({},'disable_flag'),
    ({'signature':'release_regression','schema_version':2},'rollback'),
    ({'signature':'pool_exhaustion','pool_saturated':True},'scale_pool'),
    ({'signature':'unclassified','schema_known':False},None),
    ({'schema_version':4},None),
])
def test_configured_fault_changes_verified_decision(lab,config,action):
    configure(lab,Configuration(**config))
    result=run_workflow(lab,'Judge-configured fault',False)
    assert result['verification']['status']=='passed'
    assert (result['recommendation'] or {}).get('action')==action
    assert lab.get('src-alert')['text'].find(lab.get('current')['signature'])>=0
    assert str(lab.get('migration')['schema']) in lab.get('src-deploy')['text']

@pytest.mark.parametrize('config',[{'schema_version':0},{'error_rate':51},{'signature':'arbitrary-code'},{'unexpected':True}])
def test_invalid_configuration_rejected(config):
    with pytest.raises(ValidationError):Configuration(**config)


def prepare(lab):
    run=run_workflow(lab,'Verify a safe remedy',False)
    attempt=propose(lab,run['recommendation']['action'],str(uuid4()),run['run_id'])
    approve(lab,attempt['id'])
    return attempt


def test_approval_drift_rejects_without_observed_remediation(lab):
    attempt=prepare(lab)
    configure(lab,Configuration(schema_version=4))
    before=lab.get('current')
    with pytest.raises(Conflict):execute(lab,attempt['id'])
    assert lab.get(attempt['id'])['status']=='invalidated'
    assert lab.get('current')==before and lab.lessons()==[]
    assert lab.get('outcome-'+attempt['id']) is None
    assert current_digest(lab)!=attempt['state_hash']


def test_memory_conditions_and_current_execution_eligibility_are_distinct(lab):
    attempt=prepare(lab);execute(lab,attempt['id'])
    original_source=lab.get(lab.lessons()[0]['source_id'])
    resolved=snapshot(lab)['lessons'][0]
    assert resolved['condition_matches'] and not resolved['eligible_now']
    configure(lab,Configuration())
    assert snapshot(lab)['lessons'][0]['eligible_now']
    configure(lab,Configuration(schema_version=4))
    changed=snapshot(lab)['lessons'][0]
    assert not changed['condition_matches'] and not changed['eligible_now']
    assert 'recorded v3, current v4' in changed['mismatches'][0]
    assert lab.get(original_source['id'])==original_source
    configure(lab,Configuration())
    assert snapshot(lab)['lessons'][0]['eligible_now']


def test_lab_graphs_are_separate_and_reset_is_scoped(lab):
    other=lab_store(uuid4())
    try:
        original=current_digest(other)
        configure(lab,Configuration(schema_version=4))
        assert current_digest(other)==original
        lab.reset()
        assert current_digest(other)==original and lab.get('migration')['schema']==3
    finally:other.graph.delete()


def test_http_race_returns_real_409_and_validates_uuid():
    id=uuid4();s=lab_store(id);client=TestClient(app);base=f'/api/lab/{id}'
    try:
        assert client.get('/api/lab/not-a-uuid').status_code==422
        assert client.post(base+'/configure',json={'schema_version':99}).status_code==422
        r=client.post(base+'/investigate').json()
        p=client.post(base+'/proposals',json={'action':'disable_flag','session_id':str(uuid4()),'run_id':r['run_id']})
        assert p.status_code==200
        path=base+'/proposals/'+p.json()['id']
        assert client.post(path+'/execute').status_code==409
        assert client.post(path+'/approve').status_code==200
        assert client.post(base+'/configure',json={'schema_version':4}).status_code==200
        assert client.post(path+'/execute').status_code==409
        state=client.get(base).json()
        assert state['incident']['error_rate']==18.4
        assert next(a for a in state['attempts'] if a['id']==p.json()['id'])['status']=='invalidated'
    finally:s.graph.delete()


def test_lab_api_preserves_main_scenario(monkeypatch):
    from backend.main import store_for
    monkeypatch.setenv('FALKORDB_GRAPH','lab_isolation_'+uuid4().hex)
    primary=store_for('checkout');id=uuid4();s=lab_store(id)
    try:
        before=current_digest(primary)
        client=TestClient(app)
        assert client.post(f'/api/lab/{id}/configure',json={'signature':'pool_exhaustion','pool_saturated':True}).status_code==200
        assert client.post(f'/api/lab/{id}/reset').status_code==200
        assert current_digest(primary)==before
    finally:s.graph.delete();primary.graph.delete()
