"""Verify the deployed lab through HTTPS without modifying a main scenario."""
import json
import sys
from pathlib import Path
from uuid import uuid4
import httpx


def main():
    access=dict(line.split(': ',1) for line in Path(sys.argv[1]).read_text().splitlines() if ': ' in line)
    with httpx.Client(base_url=access['URL'],auth=(access['Username'],access['Password']),headers={'Origin':access['URL']},timeout=45) as c:
        def req(method,path,**kw):
            r=c.request(method,path,**kw);r.raise_for_status();return r.json()
        original=req('GET','/api/checkout/snapshot')
        base='/api/lab/'+str(uuid4())
        state=req('GET',base)
        run=req('POST',base+'/investigate')
        p=req('POST',base+'/proposals',json={'action':run['recommendation']['action'],'session_id':str(uuid4()),'run_id':run['run_id']})
        path=base+'/proposals/'+p['id']
        req('POST',path+'/approve')
        req('POST',path+'/execute')
        assert req('GET',base)['incident']['error_rate']==.2
        state=req('POST',base+'/configure',json={})
        assert state['lessons'][0]['eligible_now']
        run=req('POST',base+'/investigate')
        p=req('POST',base+'/proposals',json={'action':run['recommendation']['action'],'session_id':str(uuid4()),'run_id':run['run_id']})
        path=base+'/proposals/'+p['id'];req('POST',path+'/approve')
        req('POST',base+'/configure',json={'schema_version':4})
        assert c.post(path+'/execute').status_code==409
        state=req('GET',base)
        assert state['incident']['error_rate']==18.4
        assert next(a for a in state['attempts'] if a['id']==p['id'])['status']=='invalidated'
        assert not state['lessons'][0]['condition_matches']
        assert req('GET','/api/checkout/snapshot')==original
        report={'url':access['URL'],'verified_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'workflow':'passed','observed_recovery':.2,'lesson_eligible_on_recurrence':True,'stale_execution_http':409,'proposal':'invalidated','errors_unchanged_after_rejection':18.4,'lesson_rejected_after_schema_drift':True,'main_scenario_preserved':True}
        req('POST',base+'/reset')
        Path('artifacts/proof-lab-deployment-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))

if __name__=='__main__':main()
