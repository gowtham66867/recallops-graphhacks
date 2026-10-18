"""Source-linked operator reports and version-bound, audience-specific handoffs."""
import json
import re
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field
from .store import now
from .engine import Conflict, check_actions, context
from .evidence import current_digest

Audience=Literal['internal','anonymized']

class ReportInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    text:str=Field(min_length=1,max_length=2000)
    category:Literal['observation','prior_attempt','correction','gap']='observation'
    outcome:Literal['unknown','unresolved','reported_resolved']='unknown'
    language:Literal['en-IN','hi-IN','kn-IN','hi-Latn']='en-IN'
    supersedes:str|None=Field(default=None,pattern=r'^report-[a-f0-9]{32}$')


def redact(text):
    text=re.sub(r'\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|AIza[A-Za-z0-9_-]{20,})\b','[credential redacted]',text)
    text=re.sub(r'(?i)\b(password|api[_ -]?key|token|secret)\s*[:=]\s*\S+',r'\1=[redacted]',text)
    text=re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~-]+','Bearer [redacted]',text)
    text=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[email redacted]',text)
    return text


def reports(store):
    return sorted([json.loads(r[0]) for r in store.query('MATCH (n:Entity) WHERE n.kind=$kind RETURN n.data LIMIT 50',{'kind':'OperatorReport'})],key=lambda n:(n['at'],n['id']))


def add_report(store,body):
    text=redact(body.text.strip())
    if not text:raise ValueError('Enter an observation or prior attempt.')
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        if len(reports(store))>=40:raise Conflict('This scenario has reached its 40-report context budget. Export reviewed context before resetting it.')
        prior=store.get(body.supersedes) if body.supersedes else None
        if body.supersedes and (not prior or prior.get('kind')!='OperatorReport' or not prior.get('active')):
            raise Conflict('Correction must reference an active operator report in this scenario.')
        if body.category=='correction' and not prior:raise ValueError('Select the report this correction replaces.')
        if prior and body.category!='correction':raise ValueError('Only a correction can supersede a report.')
        id='report-'+uuid4().hex;source_id='source-'+id;at=now()
        report={'id':id,'kind':'OperatorReport','title':'Operator '+body.category.replace('_',' '),'text':text,'quote':text,'classification':'operator_report','verified':False,'active':True,'category':body.category,'outcome':body.outcome,'language':body.language,'supersedes':body.supersedes,'source_id':source_id,'at':at}
        source={'id':source_id,'kind':'Source','title':report['title'],'text':text,'classification':'operator_report','verified':False,'at':at}
        nodes=[report,source]
        if prior:prior['active']=False;nodes.append(prior)
        store.query('UNWIND $nodes AS row MERGE (n:Entity {id:row.id}) SET n.kind=row.kind,n.title=row.title,n.data=row.data,n.updated_at=$at',{'nodes':[{'id':n['id'],'kind':n['kind'],'title':n['title'],'data':json.dumps(n)} for n in nodes],'at':at})
        store.link(id,'SUPPORTED_BY',source_id);store.link(id,'APPLIES_TO','checkout')
        return report


def redact_report(store,id):
    with store.db.connection.lock(store.name+':privacy',timeout=180,blocking_timeout=1):
        return _redact_report(store,id)

def _redact_report(store,id):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        report=store.get(id)
        if not report or report.get('kind')!='OperatorReport':raise Conflict('Operator report not found.')
        report.update(text='[operator redacted]',quote='[operator redacted]',active=False,redacted_at=now())
        source=store.get(report['source_id']);source['text']='[operator redacted]'
        # Remove retained copies in review packets and saved run snapshots/results.
        # Stale approvals are invalidated by the changed source digest.
        store.query('MATCH (n:Entity) WHERE n.kind IN $kinds DETACH DELETE n',{'kinds':['ReviewPacket','InvestigationRun','Checkpoint']})
        store.put(report);store.put(source)
        return {'status':'redacted','saved_reviews_removed':True,'downloaded_copies_recallable':False}


def create_packet(store):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        i,d,m=context(store);checks=check_actions(store);notes=reports(store)
        facts=store.fact_snapshot();sources=[{'id':n['id'],'quote':n['text'],'classification':n.get('classification','synthetic_observation'),'synthetic':True} for n in facts['nodes'] if n['kind']=='Source']
        unknowns=['Production impact and recovery are unverified; this handoff uses synthetic records and unverified operator reports.']+[c['reason'] for c in checks if c['status']=='unknown']
        active=[n for n in notes if n['active']]
        for n in active:
            if n['category']=='gap':unknowns.append(n['text'])
        packet={'id':'packet-'+uuid4().hex,'kind':'ReviewPacket','title':'Incident handoff for human review','created_at':now(),'state_hash':current_digest(store),'approvals':{},'human_review_requested':True,'internal':{'synthetic':True,'incident':i,'deployment':d,'migration':m,'checks':checks,'operator_reports':notes,'sources':sources,'lessons':store.lessons(),'prior_attempts':store.history(),'unknowns':unknowns,'human_review_requested':True,'ticket_sent':False},'anonymized':{'synthetic':True,'incident_resolved':i['status']=='resolved','source_count':len(sources),'operator_report_count':len(active),'prior_outcome_count':len(store.history()),'lesson_count':len(store.lessons()),'unknown_action_count':sum(c['status']=='unknown' for c in checks),'human_review_requested':True,'ticket_sent':False,'notice':'Raw text, source IDs, incident identifiers, precise metrics, and operator details omitted. Aggregate data may still require disclosure review.'}}
        store.put(packet)
        return packet


def packet_for(store,id):
    p=store.get(id)
    if not p or p.get('kind')!='ReviewPacket':raise Conflict('Review packet not found. Generate a new handoff.')
    if p['state_hash']!=current_digest(store):raise Conflict('Incident context changed. Generate and review a fresh handoff before exporting.')
    return p


def approve_packet(store,id,audience):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        p=packet_for(store,id);p['approvals'][audience]={'at':now(),'state_hash':p['state_hash']};store.put(p)
        return {'id':p['id'],'audience':audience,'approved':True,'state_hash':p['state_hash']}


def export_packet(store,id,audience):
    with store.db.connection.lock(store.name+':mutation',timeout=20,blocking_timeout=5):
        p=packet_for(store,id)
        if p['approvals'].get(audience,{}).get('state_hash')!=p['state_hash']:raise Conflict('This audience requires explicit approval of the current handoff.')
        return p[audience]
