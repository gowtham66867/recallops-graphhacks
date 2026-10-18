import json
import os
import re
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
from falkordb import FalkorDB
from dotenv import load_dotenv
from .fixtures import SCENARIOS, SERVICES, ACTIONS

# Never discover a parent project's credentials implicitly.
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

def now():
    return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self, scenario='checkout', prefix=None):
        if scenario not in SCENARIOS:
            raise ValueError('Unknown scenario')
        self.scenario = scenario
        base = prefix or os.getenv('FALKORDB_GRAPH', 'recallops')
        if not re.fullmatch(r'[a-zA-Z0-9_]+', base):
            raise ValueError('Graph prefix must contain letters, numbers or underscores')
        self.name = base + '_' + scenario.replace('-', '_')
        self.db = FalkorDB(host=os.getenv('FALKORDB_HOST', '127.0.0.1'), port=int(os.getenv('FALKORDB_PORT', '6389')), socket_timeout=5, socket_connect_timeout=3)
        self.graph = self.db.select_graph(self.name)

    def query(self, query, params=None):
        return self.graph.query(query, params=params or {}, timeout=3000).result_set

    def get(self, id):
        rows = self.query('MATCH (n:Entity {id:$id}) RETURN n.data LIMIT 1', {'id': id})
        return json.loads(rows[0][0]) if rows else None

    def put(self, node):
        self.query('MERGE (n:Entity {id:$id}) SET n.data=$data, n.kind=$kind, n.title=$title,n.updated_at=$updated', {'id': node['id'], 'data': json.dumps(node), 'kind': node['kind'], 'title': node['title'],'updated':node.get('updated_at',node.get('at',node.get('created_at','')))})
        return node

    def link(self, start, rel, end):
        if rel not in {'DEPENDS_ON','AFFECTS','DEPLOYED_TO','INTRODUCED','ATTEMPTED','RESULTED_IN','SUPPORTED_BY','LEARNED_FROM','APPLIES_TO','RECORDED_IN','USED_ACTION','CHECKPOINTED','PRODUCED','JUSTIFIED_BY'}:
            raise ValueError('Invalid relationship')
        self.query(f'MATCH (a:Entity {{id:$a}}), (b:Entity {{id:$b}}) MERGE (a)-[:{rel}]->(b)', {'a':start, 'b':end})

    def seed(self):
        # Redis lock serializes first initialization across API workers.
        with self.db.connection.lock(self.name + ':seed', timeout=20, blocking_timeout=5):
            if self.get('initialized'):
                return
            cfg = SCENARIOS[self.scenario]
            for id, title, team in SERVICES:
                self.put({'id':id,'kind':'Service','title':title,'team':team})
            for a,b in [('storefront','checkout'),('checkout','payments'),('checkout','orders'),('orders','postgres'),('payments','postgres'),('inventory','postgres')]:
                self.link(a,'DEPENDS_ON',b)
            if cfg.get('extra_dependency'):
                self.link('checkout','DEPENDS_ON','inventory')
            nodes = [
                {'id':'current','kind':'Incident','title':'Checkout errors after deployment','code':'INC-024','status':'investigating','revision':1,'signature':cfg['signature'],'error_rate':cfg['error_rate'],'flag_enabled':cfg['flag'],'pool_saturated':cfg['pool'],'schema_known':cfg['known'],'opened_at':'2026-10-17T16:32:00Z','environment':'production simulation'},
                {'id':'deploy-current','kind':'Deployment','title':'Checkout v2.8.0','version':'v2.8.0','schema':cfg['schema'],'previous_schema':cfg['rollback_schema'],'stable_path_schemas':[2,3],'at':'2026-10-17T16:29:00Z'},
                {'id':'migration','kind':'Migration','title':f'Schema v{cfg["schema"]}' if cfg['known'] else 'Schema unverified','schema':cfg['schema'],'at':'2026-10-17T16:28:00Z'},
                {'id':'flag','kind':'FeatureFlag','title':'express_checkout_v2','enabled':cfg['flag']},
                {'id':'inc-017','kind':'Incident','title':'Restart did not resolve errors','code':'INC-017','signature':'feature_contract','at':'2026-10-14T10:00:00Z'},
                {'id':'attempt-017','kind':'ActionAttempt','title':'Restart checkout','action':'restart','status':'failed','at':'2026-10-14T10:04:00Z'},
                {'id':'outcome-017','kind':'Outcome','title':'Errors persisted after restart','status':'failed','error_before':17.8,'error_after':17.8},
                {'id':'inc-021','kind':'Incident','title':'Rollback restored checkout','code':'INC-021','signature':'release_regression','at':'2026-10-16T12:00:00Z'},
                {'id':'attempt-021','kind':'ActionAttempt','title':'Roll back checkout','action':'rollback','status':'succeeded','schema':2,'at':'2026-10-16T12:05:00Z'},
                {'id':'outcome-021','kind':'Outcome','title':'Recovered on schema v2','status':'succeeded','schema':2,'error_before':14.2,'error_after':0.2},
                {'id':'src-alert','kind':'Source','title':'Alert · checkout error budget','text':f'SYNTHETIC telemetry: checkout error rate {cfg["error_rate"]}%. Failure signature: {cfg["signature"]}. Express checkout flag: {cfg["flag"]}. Pool saturation: {cfg["pool"]}.','at':'2026-10-17T16:32:00Z','classification':'observed'},
                {'id':'src-deploy','kind':'Source','title':'Deployment manifest · v2.8.0','text':f'SYNTHETIC manifest: checkout v2.8.0; current schema {cfg["schema"]}; previous application requires schema {cfg["rollback_schema"]}. Stable checkout path supports schemas v2 and v3. Schema telemetry verified: {cfg["known"]}.','at':'2026-10-17T16:29:00Z','classification':'observed'},
                {'id':'src-017','kind':'Source','title':'Postmortem · INC-017','text':'SYNTHETIC postmortem: feature_contract failures. Restarting workers left errors unchanged at 17.8%. The deployment and feature settings did not change.','at':'2026-10-14T11:00:00Z','classification':'observed'},
                {'id':'src-021','kind':'Source','title':'Postmortem · INC-021','text':'SYNTHETIC postmortem: release_regression on schema v2. Rollback to v2.7.0 reduced errors from 14.2% to 0.2%. This result was observed only with schema v2.','at':'2026-10-16T13:00:00Z','classification':'observed'},
            ]
            for key, action in ACTIONS.items():
                self.put({'id':'action-'+key,'kind':'ActionDefinition',**action,'action':key})
            for node in nodes:
                self.put(node)
            for a,r,b in [('current','AFFECTS','checkout'),('deploy-current','DEPLOYED_TO','checkout'),('deploy-current','INTRODUCED','migration'),('deploy-current','INTRODUCED','flag'),('current','SUPPORTED_BY','src-alert'),('deploy-current','SUPPORTED_BY','src-deploy'),('migration','SUPPORTED_BY','src-deploy'),('inc-017','AFFECTS','checkout'),('inc-017','ATTEMPTED','attempt-017'),('attempt-017','RESULTED_IN','outcome-017'),('outcome-017','SUPPORTED_BY','src-017'),('inc-021','AFFECTS','checkout'),('inc-021','ATTEMPTED','attempt-021'),('attempt-021','RESULTED_IN','outcome-021'),('outcome-021','SUPPORTED_BY','src-021')]:
                self.link(a,r,b)
            self.put({'id':'initialized','kind':'Metadata','title':'Seed complete','at':now()})

    def snapshot(self):
        rows = self.query('MATCH (n:Entity) WHERE NOT n.kind IN $hidden RETURN n.data LIMIT 200', {'hidden':['Metadata','Session','InvestigationRun','Checkpoint','ReviewPacket']})
        nodes = [json.loads(row[0]) for row in rows]
        edges = [{'source':a,'target':b,'label':r} for a,r,b in self.query('MATCH (a:Entity)-[r]->(b:Entity) RETURN a.id,type(r),b.id LIMIT 400')]
        return {'nodes':nodes,'edges':edges}

    def fact_snapshot(self):
        """A bounded factual view, unaffected by appended investigation checkpoints."""
        kinds=['Service','Incident','Deployment','Migration','FeatureFlag','ActionAttempt','Outcome','Source','Lesson','OperatorReport']
        nodes=[json.loads(r[0]) for r in self.query('MATCH (n:Entity) WHERE n.kind IN $kinds RETURN n.data LIMIT 501', {'kinds':kinds})]
        if len(nodes)>500:
            raise ValueError('Evidence budget exceeded. Archive old incidents before investigating.')
        # Draft proposals do not invalidate the context that justified creating them.
        nodes=[n for n in nodes if n['kind']!='ActionAttempt' or n.get('status') in {'succeeded','failed','inconclusive'}]
        ids={n['id'] for n in nodes}
        edges=[{'source':a,'target':b,'label':r} for a,r,b in self.query('MATCH (a:Entity)-[r]->(b:Entity) WHERE a.kind IN $kinds AND b.kind IN $kinds RETURN a.id,type(r),b.id LIMIT 1001', {'kinds':kinds})]
        if len(edges)>1000:
            raise ValueError('Evidence relationship budget exceeded.')
        return {'nodes':nodes,'edges':[e for e in edges if e['source'] in ids and e['target'] in ids]}

    def dependencies(self):
        rows = self.query('MATCH p=(a:Entity {id:$id})-[:DEPENDS_ON*1..4]->(b:Entity) RETURN b.data, length(p) LIMIT 30', {'id':'checkout'})
        return [{'service':json.loads(data),'hops':hops} for data,hops in rows]

    def history(self):
        rows = self.query('MATCH (c:Entity {id:$id})-[:AFFECTS]->(s:Entity)<-[:AFFECTS]-(i:Entity)-[:ATTEMPTED]->(a:Entity)-[:RESULTED_IN]->(o:Entity)-[:SUPPORTED_BY]->(src:Entity) RETURN i.data,a.data,o.data,src.data ORDER BY a.id LIMIT 30', {'id':'current'})
        return [{'incident':json.loads(i),'attempt':json.loads(a),'outcome':json.loads(o),'source':json.loads(src)} for i,a,o,src in rows]

    def lessons(self):
        return [json.loads(row[0]) for row in self.query('MATCH (l:Entity)-[:APPLIES_TO]->(s:Entity {id:$id}) WHERE l.kind=$kind RETURN l.data ORDER BY l.id DESC LIMIT 20', {'id':'checkout','kind':'Lesson'})]

    def sources_for(self,id):
        return [json.loads(row[0]) for row in self.query('MATCH (:Entity {id:$id})-[:SUPPORTED_BY]->(s:Entity) WHERE s.kind=$kind RETURN s.data LIMIT 40',{'id':id,'kind':'Source'})]

    def runs(self):
        rows=self.query("MATCH (r:Entity) WHERE r.kind=$kind RETURN r.data ORDER BY coalesce(r.updated_at,'') DESC LIMIT 20",{'kind':'InvestigationRun'})
        runs=[json.loads(row[0]) for row in rows]
        runs.sort(key=lambda r:r.get('updated_at',''),reverse=True)
        return [{k:r.get(k) for k in ['id','status','phase','updated_at','resume_count','live']} for r in runs]

    def proposals(self):
        return [json.loads(row[0]) for row in self.query('MATCH (i:Entity {id:$id})-[:ATTEMPTED]->(a:Entity) RETURN a.data ORDER BY a.id DESC LIMIT 20', {'id':'current'})]

    def reset(self):
        if self.db.connection.exists(self.name):
            self.graph.delete()
        self.seed()
