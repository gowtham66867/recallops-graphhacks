"""Deterministic applicability checks and state-dependent simulation. No LLM authority over execution."""
import json
from uuid import uuid4
from .store import now
from .fixtures import ACTIONS

class Conflict(Exception):
    pass

def context(store):
    rows = store.query('MATCH (i:Entity {id:$id})-[:AFFECTS]->(s:Entity)<-[:DEPLOYED_TO]-(d:Entity)-[:INTRODUCED]->(m:Entity) WHERE m.kind=$kind RETURN i.data,d.data,m.data LIMIT 1', {'id':'current','kind':'Migration'})
    if not rows:
        raise Conflict('Current deployment evidence is missing. Re-seed this scenario.')
    i,d,m = (json.loads(v) for v in rows[0])
    return i,d,m

def check_actions(store):
    incident, deploy, migration = context(store)
    history = store.history()
    lessons = store.lessons()
    operational_sources=list(dict.fromkeys(s['id'] for id in ['current','deploy-current'] for s in store.sources_for(id)))
    results = []
    for key, action in ACTIONS.items():
        evidence = ['current','checkout','deploy-current','src-alert',*operational_sources]
        status, reason = 'unknown', 'Insufficient evidence to establish action preconditions.'
        if incident['status'] == 'resolved':
            status, reason = 'contradicted', 'This incident is resolved. No further remediation is needed.'
        elif key == 'restart':
            matching = [h for h in history if h['attempt']['action'] == key and h['incident']['signature'] == incident['signature'] and h['outcome']['status'] == 'failed']
            if matching:
                codes=', '.join(sorted({h['incident'].get('code',h['incident']['id']) for h in matching}))
                status, reason = 'contradicted', f'Restart failed for the same failure signature in {codes}; there is no new evidence that recycling workers addresses this fault.'
                for h in matching:
                    evidence += [h['incident']['id'],h['attempt']['id'],h['outcome']['id'],h['source']['id']]
            else:
                reason = 'No evidence of a transient worker fault. A restart is not justified by the available observations.'
        elif key == 'rollback':
            evidence += ['migration','src-deploy']
            prior=[h for h in history if h['attempt']['action']==key and h['outcome']['status']=='succeeded']
            for h in prior:
                evidence += [h['incident']['id'],h['attempt']['id'],h['outcome']['id'],h['source']['id']]
            compatible_prior=[h for h in prior if h['incident']['signature']==incident['signature'] and h['outcome'].get('schema',h['attempt'].get('schema'))==migration['schema']]
            if not incident['schema_known']:
                reason = 'Current schema is unverified. Historical rollback success cannot establish compatibility.'
            elif migration['schema'] != deploy['previous_schema']:
                status, reason = 'contradicted', f'Rollback requires schema v{deploy["previous_schema"]}; current schema is v{migration["schema"]}. Historical rollback success cannot override this mismatch.'
            elif incident['signature'] == 'release_regression' and compatible_prior:
                codes=', '.join(sorted({h['incident'].get('code',h['incident']['id']) for h in compatible_prior}))
                status, reason = 'supported', f'Schema v{migration["schema"]} matches the previous application. The current failure signature matches observed rollback recovery in {codes}.'
            elif incident['signature'] == 'release_regression':
                reason = 'Schema is compatible, but no graph-retrieved successful rollback matches this failure signature and schema. Historical justification is missing.'
            else:
                reason = 'Schema is compatible, but evidence does not link the current failure to the release.'
        elif key == 'disable_flag':
            evidence += ['flag','migration','src-deploy']
            if not incident['flag_enabled']:
                status, reason = 'contradicted', 'Express checkout is already disabled.'
            elif not incident['schema_known'] or migration['schema'] not in deploy.get('stable_path_schemas',[]):
                reason = 'Stable-path schema compatibility is unverified. Do not infer that disabling the flag is safe.'
            elif incident['signature'] == 'feature_contract':
                status, reason = 'supported', 'Express checkout is enabled and telemetry identifies a feature-contract failure. Disabling it routes traffic through the schema-compatible stable path.'
            elif incident['signature'] == 'pool_exhaustion':
                status, reason = 'contradicted', 'Observed connection exhaustion is unrelated to the express checkout flag; disabling it does not increase pool capacity.'
        elif key == 'scale_pool':
            if incident['pool_saturated'] and incident['signature'] == 'pool_exhaustion':
                status, reason = 'supported', 'Telemetry shows pool saturation and connection-exhaustion errors. Increasing capacity addresses the observed bottleneck in this simulator.'
            elif not incident['pool_saturated']:
                status, reason = 'contradicted', 'The connection pool is not saturated. Additional capacity does not address this failure.'
        applicable = [l for l in lessons if l['action']==key and l['signature']==incident['signature'] and l['schema']==migration['schema'] and l['status']=='succeeded']
        if applicable and status=='supported':
            lesson=applicable[0]
            reason+=' A prior observed success in this workspace matches the current signature and schema; its conditions were revalidated.'
            evidence += [lesson['id'],lesson['source_id'],lesson['attempt_id'],'outcome-'+lesson['attempt_id']]
        results.append({'action':key,**action,'status':status,'reason':reason,'evidence':list(dict.fromkeys(evidence)), 'recalled_lesson_ids':[l['id'] for l in applicable] if status=='supported' else [], 'preconditions': {'disable_flag':['Flag enabled','Feature-contract failure observed','Stable path supports current schema'], 'rollback':['Schema verified','Previous version supports current schema','Release regression observed'], 'restart':['Evidence of recoverable worker fault','No unresolved matching failure'], 'scale_pool':['Pool saturated','Connection exhaustion observed']}[key]})
    return results

def investigate(store):
    checks = check_actions(store)
    supported = [c for c in checks if c['status']=='supported']
    selected = supported[0] if supported else None
    incident,_,_ = context(store)
    return {'checks':checks,'recommendation':selected,'revision':incident['revision'],'lessons':store.lessons(), 'dependencies':store.dependencies(), 'history':store.history()}

def propose(store, action, session_id, run_id=None):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        if run_id:
            from .workflow import validate_handoff
            validate_handoff(store,run_id,action)
        checks = {c['action']:c for c in check_actions(store)}
        if action not in checks or checks[action]['status'] != 'supported':
            raise Conflict('Action is not supported by the current evidence.')
        incident = store.get('current')
        from .evidence import current_digest
        attempt = {'id':'attempt-'+uuid4().hex, 'kind':'ActionAttempt','title':ACTIONS[action]['title'],'action':action,'status':'proposed','revision':incident['revision'],'session_id':session_id,'at':now(),'evidence':checks[action]['evidence'],'state_hash':current_digest(store),'run_id':run_id}
        store.put(attempt)
        store.link('current','ATTEMPTED',attempt['id'])
        store.link(attempt['id'],'USED_ACTION','action-'+action)
        store.link(attempt['id'],'RECORDED_IN',session_id)
        if run_id:store.link(attempt['id'],'JUSTIFIED_BY',run_id)
        return attempt

def approve(store, id):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        attempt = store.get(id)
        if not attempt or attempt['kind'] != 'ActionAttempt' or not id.startswith('attempt-') or 'revision' not in attempt:
            raise Conflict('Unknown proposal.')
        if attempt['status'] in {'approved','succeeded','failed','inconclusive'}:
            return attempt
        if attempt['status'] != 'proposed':
            raise Conflict('Proposal cannot be approved in its current state.')
        incident = store.get('current')
        from .evidence import current_digest
        if incident['revision'] != attempt['revision'] or attempt.get('state_hash')!=current_digest(store):
            attempt['status']='invalidated'
            store.put(attempt)
            raise Conflict('State changed after proposal. Investigate again before approval.')
        attempt['status']='approved'
        attempt['approved_at']=now()
        return store.put(attempt)

def simulate(incident, action):
    updated = dict(incident)
    # Transition rules operate on state. Unknown signatures never silently recover.
    if action == 'disable_flag':
        updated['flag_enabled']=False
        if incident['signature']=='feature_contract':
            updated['error_rate']=0.2
    elif action == 'rollback' and incident['signature']=='release_regression':
        updated['error_rate']=0.2
    elif action == 'scale_pool':
        updated['pool_saturated']=False
        if incident['signature']=='pool_exhaustion':
            updated['error_rate']=0.3
    recovered = updated['error_rate'] < 1
    improved = updated['error_rate'] < incident['error_rate']
    status = 'succeeded' if recovered else 'inconclusive' if improved else 'failed'
    updated['status']='resolved' if recovered else 'investigating'
    updated['revision']+=1
    return updated,status

def execute(store,id):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        attempt = store.get(id)
        if not attempt or 'revision' not in attempt:
            raise Conflict('Unknown proposal.')
        if attempt['status'] in {'succeeded','failed','inconclusive'}:
            return attempt  # Idempotent retry returns the same durable result.
        if attempt['status'] != 'approved':
            raise Conflict('Explicit approval is required before simulation.')
        incident = store.get('current')
        checks = {c['action']:c for c in check_actions(store)}
        from .evidence import current_digest
        if incident['revision'] != attempt['revision'] or attempt.get('state_hash')!=current_digest(store) or checks[attempt['action']]['status'] != 'supported':
            attempt['status']='invalidated'
            store.put(attempt)
            raise Conflict('State changed or preconditions no longer hold. Run a new investigation.')
        updated,status = simulate(incident,attempt['action'])
        stamp = now()
        attempt.update({'status':status,'executed_at':stamp,'completed_at':stamp,'transitions':['proposed','approved','executing',status]})
        source = {'id':'source-'+id,'kind':'Source','title':'Simulator observation · '+attempt['title'],'at':stamp,'classification':'observed','text':f'SYNTHETIC execution. Action: {attempt["action"]}. Before: {incident["error_rate"]}%. After: {updated["error_rate"]}%. Outcome: {status}. Signature: {incident["signature"]}. No production systems were contacted.'}
        outcome = {'id':'outcome-'+id,'kind':'Outcome','title':f'Errors {incident["error_rate"]}% → {updated["error_rate"]}%','status':status,'error_before':incident['error_rate'],'error_after':updated['error_rate'],'at':stamp}
        lesson = {'id':'lesson-'+id,'kind':'Lesson','title':attempt['title']+' · '+status,'text':f'{attempt["title"]} {status} for {incident["signature"]} on schema {store.get("migration")["schema"]}. Observed error rate: {incident["error_rate"]}% → {updated["error_rate"]}%. Recheck conditions before reuse.','signature':incident['signature'],'schema':store.get('migration')['schema'],'action':attempt['action'],'at':stamp,'source_id':source['id'],'attempt_id':id,'classification':'observed','status':status}
        flag = dict(store.get('flag'),enabled=updated['flag_enabled'])
        deployment=store.get('deploy-current')
        if attempt['action']=='rollback' and status=='succeeded':
            deployment.update(version='v2.7.0',title='Checkout v2.7.0')
        source['observed_state']={'deployment':deployment['version'],'schema':store.get('migration')['schema'],'flag_enabled':updated['flag_enabled'],'error_rate':updated['error_rate']}
        source['text']+=f' Observed deployment after action: {deployment["version"]}; express checkout enabled: {updated["flag_enabled"]}.'
        # All state, outcome, and memory are committed in ONE graph query. A process
        # crash cannot apply the simulator transition without recording its outcome.
        params={'current':json.dumps(updated),'id':id,'attempt':json.dumps(attempt),'flag':json.dumps(flag),'deployment':json.dumps(deployment),'deployment_title':deployment['title']}
        query='MATCH (i:Entity {id:"current"}), (a:Entity {id:$id}), (f:Entity {id:"flag"}), (d:Entity {id:"deploy-current"}) SET i.data=$current,a.data=$attempt,f.data=$flag,d.data=$deployment,d.title=$deployment_title '
        for alias,node in [('o',outcome),('s',source),('l',lesson)]:
            params[alias+'id']=node['id']; params[alias+'data']=json.dumps(node);params[alias+'title']=node['title'];params[alias+'kind']=node['kind']
            query+=f'CREATE ({alias}:Entity {{id:${alias}id,data:${alias}data,title:${alias}title,kind:${alias}kind}}) '
        query+='CREATE (a)-[:RESULTED_IN]->(o), (o)-[:SUPPORTED_BY]->(s), (i)-[:SUPPORTED_BY]->(s), (d)-[:SUPPORTED_BY]->(s), (f)-[:SUPPORTED_BY]->(s), (l)-[:LEARNED_FROM]->(o), (l)-[:APPLIES_TO]->(i) WITH l MATCH (svc:Entity {id:"checkout"}) CREATE (l)-[:APPLIES_TO]->(svc)'
        store.query(query,params)
        return attempt

def change_state(store):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        i = store.get('current')
        i['revision']+=1
        i['schema_known']=False
        store.put(i)
        return i

def recur(store):
    """Reintroduce synthetic fault conditions while preserving observed experience."""
    from .fixtures import SCENARIOS
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        i=store.get('current')
        if i['status']!='resolved':
            raise Conflict('Resolve this incident before replaying it with memory.')
        cfg=SCENARIOS[store.scenario]
        i.update(status='investigating',revision=i['revision']+1,flag_enabled=cfg['flag'],pool_saturated=cfg['pool'],error_rate=cfg['error_rate'])
        store.put(i)
        store.put(dict(store.get('flag'),enabled=cfg['flag']))
        return i
