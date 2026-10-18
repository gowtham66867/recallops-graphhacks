"""Architecture evidence and graph-memory ablation, using disposable real graphs.

This is a deterministic context ablation, not an LLM performance experiment.
"""
import json
from pathlib import Path
from uuid import uuid4
from backend.store import Store,now
from backend.workflow import run_workflow
from backend.engine import check_actions,propose,approve,execute,Conflict
from backend.evidence import current_digest


def main():
    prefix='architecture_eval_'+uuid4().hex
    cases=[];ablations=[]
    for scenario in ['checkout','rollback-valid']:
        s=Store(scenario,prefix=prefix);s.seed()
        try:
            before=check_actions(s)
            s.query('MATCH (i:Entity)-[r:AFFECTS]->(:Entity {id:$service}) WHERE i.id <> $current DELETE r',{'service':'checkout','current':'current'})
            s.query('MATCH (l:Entity)-[r:APPLIES_TO]->(:Entity {id:$service}) WHERE l.kind=$kind DELETE r',{'service':'checkout','kind':'Lesson'})
            after=check_actions(s)
            target='restart' if scenario=='checkout' else 'rollback'
            a=next(c for c in before if c['action']==target);b=next(c for c in after if c['action']==target)
            ablations.append({'scenario':scenario,'action':target,'with_graph_history':a['status'],'without_history_edges':b['status'],'changed':a['status']!=b['status'],'scope':'Only traversable historical context removed; current deployment evidence preserved.'})
        finally:s.graph.delete()
    for scenario in ['checkout','rollback-valid','unknown','pool','dependency']:
        s=Store(scenario,prefix=prefix);s.seed()
        try:
            before=current_digest(s);r=run_workflow(s,'Investigate the incident and compare alternatives.')
            saved=s.get(r['run_id'])
            cases.append({'scenario':scenario,'verification':r['verification']['status'],'source_records_checked':r['verification']['source_count'],'checkpoint_count':len(saved['checkpoints']),'specialists':len(r['specialists']),'counterfactuals_non_mutating':current_digest(s)==before,'all_forecasts_labelled_predictions':all(not row['observed'] and row['classification']=='prediction' for row in r['counterfactuals']),'recommendation':(r.get('recommendation') or {}).get('action')})
        finally:s.graph.delete()
    report={'measured_at':now(),'database':'real FalkorDB v4.16.3','mode':'deterministic architecture and graph-context ablation','cases':cases,'memory_ablations':ablations,'live_model_evaluation':'A real provider request returned credit_balance_exhausted; no successful live model evaluation. Mocked contracts are not live validation.','limitations':['Synthetic observations include preassigned failure signatures.','The simulator is an explicit transition model, not a production environment.','These results do not establish general incident accuracy or superiority to another database.','Ablation changes available context; it is not a same-model performance comparison.']}
    Path('docs/architecture-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    passed=all(c['verification']=='passed' and c['checkpoint_count']==5 and c['counterfactuals_non_mutating'] and c['all_forecasts_labelled_predictions'] for c in cases) and all(a['changed'] for a in ablations)
    print(json.dumps({'passed':passed,'scenario_cases':len(cases),'memory_ablations':len(ablations),'report':'docs/architecture-evaluation.json'},indent=2))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
