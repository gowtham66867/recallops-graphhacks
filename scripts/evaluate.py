"""Reproducible real-database scenario evaluation. Never touches the user's demo graph."""
import json
import platform
import time
from pathlib import Path
from uuid import uuid4
from backend.store import Store
from backend.engine import investigate,propose,approve,execute,recur,check_actions

EXPECTED={'checkout':'disable_flag','rollback-valid':'rollback','unknown':None,'pool':'scale_pool','dependency':'disable_flag'}

def main():
    prefix='eval_'+uuid4().hex
    rows=[]
    for scenario,expected in EXPECTED.items():
        s=Store(scenario,prefix=prefix);s.seed();start=time.perf_counter()
        try:
            result=investigate(s)
            selected=(result['recommendation'] or {}).get('action')
            evidence=[id for c in result['checks'] for id in c['evidence']]
            row={'scenario':scenario,'expected':expected,'actual':selected,'decision_pass':selected==expected,'all_evidence_resolves':all(s.get(id) is not None for id in evidence),'investigation_ms':round((time.perf_counter()-start)*1000,2)}
            if selected:
                a=propose(s,selected,'evaluation');approve(s,a['id']);outcome=execute(s,a['id']);row['execution_status']=outcome['status']
                fresh=Store(scenario,prefix=prefix);fresh.seed()
                row['persistent_recall_pass']=len(fresh.lessons())==1
                row['idempotent_execution_pass']=execute(s,a['id'])==outcome and len(s.lessons())==1
                recur(s);r=investigate(fresh)
                row['conditional_reuse_pass']=bool((r['recommendation'] or {}).get('recalled_lesson_ids'))
            rows.append(row)
        finally:s.graph.delete()
    report={'measured_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'database':'Real FalkorDB v4.16.3, local Docker','mode':'deterministic applicability engine','python':platform.python_version(),'cases':rows,'live_model_evaluation':'Not run: no project OPENAI_API_KEY configured. Mock adapter contract tests do not establish model quality.','same_model_baseline':'Not run: requires configured model. No comparative model performance claims.','limitations':['Small synthetic scenario suite; not production incident accuracy.','Local timings include database round trips and evidence validation; not LLM latency.','Replay is a simulator control, not an organically recurring production incident.']}
    out=Path('docs/evaluation.json');out.write_text(json.dumps(report,indent=2)+'\n')
    passed=all(r['decision_pass'] and r['all_evidence_resolves'] and all(r.get(k,True) for k in ['persistent_recall_pass','idempotent_execution_pass','conditional_reuse_pass']) for r in rows)
    print(json.dumps({'pass':passed,'cases':len(rows),'report':str(out)},indent=2))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
