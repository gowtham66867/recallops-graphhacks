"""A browser-scoped synthetic laboratory using the production policy and executor."""
import json
import os
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from .store import Store, now
from .engine import context, check_actions
from .evidence import current_digest

class Configuration(BaseModel):
    model_config = ConfigDict(extra='forbid')
    signature:Literal['feature_contract','release_regression','pool_exhaustion','unclassified']='feature_contract'
    schema_version:int=Field(default=3,ge=1,le=5)
    previous_schema:int=Field(default=2,ge=1,le=5)
    schema_known:bool=True
    flag_enabled:bool=True
    pool_saturated:bool=False
    error_rate:float=Field(default=18.4,ge=1,le=50)


def lab_store(lab_id:UUID):
    store=Store('checkout',prefix=os.getenv('FALKORDB_GRAPH','recallops')+'_lab_'+lab_id.hex)
    store.seed()
    return store


def snapshot(store):
    incident,deploy,migration=context(store)
    checks=check_actions(store)
    lessons=[]
    for lesson in store.lessons():
        mismatches=[]
        if lesson['signature']!=incident['signature']:mismatches.append('Failure signature changed')
        if lesson['schema']!=migration['schema']:mismatches.append(f"Schema changed: recorded v{lesson['schema']}, current v{migration['schema']}")
        if not incident['schema_known']:mismatches.append('Current schema is unverified')
        if lesson['status']!='succeeded':mismatches.append('Recorded outcome was not a success')
        check=next(c for c in checks if c['action']==lesson['action'])
        lessons.append({**lesson,'condition_matches':not mismatches,'mismatches':mismatches,'eligible_now':lesson['id'] in check['recalled_lesson_ids'],'current_policy':check['reason']})
    return {'incident':incident,'deployment':deploy,'checks':checks,'lessons':lessons,'attempts':store.proposals(),'state_hash':current_digest(store),'configuration':{'signature':incident['signature'],'schema_version':migration['schema'],'previous_schema':deploy['previous_schema'],'schema_known':incident['schema_known'],'flag_enabled':incident['flag_enabled'],'pool_saturated':incident['pool_saturated'],'error_rate':incident['error_rate']},'scope':'Browser-scoped synthetic graph. Shared demo authentication; not tenant isolation.'}


def configure(store,config:Configuration):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        incident,deploy,migration=context(store)
        incident.update(signature=config.signature,schema_known=config.schema_known,flag_enabled=config.flag_enabled,pool_saturated=config.pool_saturated,error_rate=config.error_rate,status='investigating',revision=incident['revision']+1)
        deploy.update(schema=config.schema_version,previous_schema=config.previous_schema,version='v2.8.0',title='Checkout v2.8.0')
        migration.update(schema=config.schema_version,title=f'Schema v{config.schema_version}' if config.schema_known else 'Schema unverified')
        flag=store.get('flag');flag['enabled']=config.flag_enabled
        alert=store.get('src-alert');manifest=store.get('src-deploy')
        at=now()
        alert.update(text=f'SYNTHETIC lab telemetry: error rate {config.error_rate}%; signature {config.signature}; flag {config.flag_enabled}; pool saturation {config.pool_saturated}.',at=at)
        manifest.update(text=f'SYNTHETIC lab manifest: current schema {config.schema_version}; previous application requires schema {config.previous_schema}; stable path supports schemas 2 and 3; schema verified {config.schema_known}.',at=at)
        # Publish a coherent configuration and its current telemetry in one graph command.
        nodes=[incident,deploy,migration,flag,alert,manifest]
        store.query('UNWIND $nodes AS row MATCH (n:Entity {id:row.id}) SET n.data=row.data,n.title=row.title,n.updated_at=$at',{'nodes':[{'id':n['id'],'data':json.dumps(n),'title':n['title']} for n in nodes],'at':at})
    return snapshot(store)
