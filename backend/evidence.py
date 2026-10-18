"""Evidence identity, deterministic counterfactuals, and a fail-closed verifier."""
import hashlib
import json
import re
from .engine import context, check_actions, simulate


def digest(facts):
    canonical={'nodes':sorted(facts['nodes'],key=lambda n:n['id']), 'edges':sorted(facts['edges'],key=lambda e:(e['source'],e['label'],e['target']))}
    return hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def current_digest(store):
    return digest(store.fact_snapshot())


def counterfactuals(store,checks):
    incident,_,_=context(store)
    rows=[]
    for c in checks:
        row={'action':c['action'],'title':c['title'],'applicability':c['status'],'evidence':c['evidence'],'classification':'prediction','observed':False}
        if c['status']!='supported':
            row.update(verdict='blocked' if c['status']=='contradicted' else 'unknown',reason=c['reason'],predicted_error_rate=None)
        else:
            updated,status=simulate(incident,c['action'])
            row.update(verdict=status,reason='Dry-run of documented simulator transition rules, not an observed outcome.',predicted_error_rate=updated['error_rate'])
        rows.append(row)
    return rows


def verify(store,result,facts,expected_hash):
    issues=[]
    known={n['id']:n for n in facts['nodes']}
    used=set()
    for c in result['checks']:
        for id in c['evidence']:
            used.add(id)
            if id not in known:issues.append('Missing evidence: '+id)
        if not any(known.get(id,{}).get('kind')=='Source' for id in c['evidence']):
            issues.append('Decision has no original source: '+c['action'])
    fresh=check_actions(store)
    expected={c['action']:c for c in fresh}
    for c in result['checks']:
        if c['status']!=expected[c['action']]['status']:
            issues.append('Action applicability changed: '+c['action'])
    selected=result.get('recommendation')
    if selected and expected[selected['action']]['status']!='supported':
        issues.append('Recommendation does not satisfy current preconditions.')
    if current_digest(store)!=expected_hash:issues.append('Evidence changed during investigation.')
    return {'status':'passed' if not issues else 'blocked','issues':issues,'evidence_count':len(used),'source_count':sum(known.get(id,{}).get('kind')=='Source' for id in used),'state_hash':expected_hash,'scope':'Checks record existence, source linkage, unchanged context, and rule consistency. It does not establish semantic entailment of model prose.'}


def citation_check(summary,facts):
    # Only IDs from evidence actually made available to this investigation qualify.
    known={n['id'] for n in facts['nodes'] if n['kind']=='Source'}
    cited=set(re.findall(r'\[([A-Za-z0-9_-]+)\]',summary))
    invalid=sorted(cited-known)
    issues=['Unretrieved or non-source citation: '+id for id in invalid]
    if not cited:issues.append('Model explanation contains no source citations.')
    return {'passed':not issues,'issues':issues,'source_ids':sorted(cited&known)}
