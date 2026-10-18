import os
from pathlib import Path
from contextlib import asynccontextmanager
from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from redis.exceptions import RedisError,LockError
from .store import Store, now
from .fixtures import SCENARIOS
from .engine import investigate, propose, approve, execute, Conflict, change_state, recur
from .workflow import run_workflow

@asynccontextmanager
async def lifespan(app):
    yield

app=FastAPI(title='RecallOps',version='1.0.0',lifespan=lifespan)

@app.exception_handler(RedisError)
async def graph_error(request,exc):
    return JSONResponse(status_code=503,content={'detail':'FalkorDB is unavailable. Start it with docker compose up -d. No fallback data was used.'})

@app.exception_handler(Conflict)
async def conflict(request,exc):
    return JSONResponse(status_code=409,content={'detail':str(exc)})

@app.exception_handler(LockError)
async def active_run(request,exc):
    return JSONResponse(status_code=409,content={'detail':'This operation is already running or its recovery lease has not expired. Try again after the active worker finishes.'})

# Local workbench: block cross-origin writes and leave the server bound to loopback.
@app.middleware('http')
async def origin_guard(request:Request,call_next):
    origin=request.headers.get('origin')
    if request.method not in {'GET','HEAD','OPTIONS'} and origin:
        from urllib.parse import urlparse
        if urlparse(origin).netloc != request.headers.get('host'):
            # Vite's local development proxy preserves its own origin.
            if origin not in {'http://127.0.0.1:5173','http://localhost:5173'}:
                return JSONResponse(status_code=403,content={'detail':'Cross-origin mutation rejected.'})
    return await call_next(request)

def store_for(scenario):
    if scenario not in SCENARIOS: raise HTTPException(404,'Unknown scenario')
    store=Store(scenario);store.seed();return store

class Investigation(BaseModel):
    question:str=Field(default='Investigate this incident and recommend the next action.',max_length=2000)
    live:bool=False

class Proposal(BaseModel):
    action:str=Field(max_length=40)
    session_id:UUID
    run_id:str=Field(pattern=r'^run-[a-f0-9]{32}$')

@app.get('/api/health')
def health():
    s=Store();s.query('RETURN 1')
    return {'status':'ok','database':'FalkorDB','live_available':bool(os.getenv('OPENAI_API_KEY')),'model':os.getenv('OPENAI_MODEL','gpt-4.1-mini'),'synthetic':True}

@app.get('/api/scenarios')
def scenarios():
    return [{'id':id,'name':v['name'],'description':v['description']} for id,v in SCENARIOS.items()]

@app.get('/api/{scenario}/snapshot')
def snapshot(scenario:str):
    s=store_for(scenario)
    return {**s.snapshot(),'incident':s.get('current'),'lessons':s.lessons(),'attempts':s.proposals(),'scenario':SCENARIOS[scenario]['name']}

@app.post('/api/{scenario}/ablation')
def history_ablation(scenario:str):
    from .ablation import compare_history
    s=store_for(scenario)
    with s.db.connection.lock(s.name+':ablation',timeout=45,blocking_timeout=1):
        return compare_history(s)

@app.post('/api/{scenario}/investigate')
def investigation(scenario:str,body:Investigation):
    s=store_for(scenario)
    try: return run_workflow(s,body.question,body.live)
    except ValueError as e: raise HTTPException(422,str(e))
    except RedisError: raise
    except Conflict: raise
    except Exception:
        # Never return provider exceptions containing request headers or secrets.
        raise HTTPException(502,'Live model request failed. Check model access and API configuration. No action was executed.')

@app.post('/api/{scenario}/proposals')
def proposal(scenario:str,body:Proposal):
    return propose(store_for(scenario),body.action,str(body.session_id),body.run_id)

@app.get('/api/{scenario}/runs/{id}')
def investigation_run(scenario:str,id:str):
    run=store_for(scenario).get(id)
    if not run or run['kind']!='InvestigationRun':raise HTTPException(404,'Investigation run not found')
    return run

@app.get('/api/{scenario}/runs')
def investigation_runs(scenario:str):return store_for(scenario).runs()

@app.post('/api/{scenario}/runs/{id}/resume')
def resume_investigation(scenario:str,id:str):
    s=store_for(scenario);run=s.get(id)
    if not run or run['kind']!='InvestigationRun':raise HTTPException(404,'Investigation run not found')
    try:return run_workflow(s,run['question'],run['live'],run_id=id)
    except (Conflict,RedisError):raise
    except ValueError as e:raise HTTPException(422,str(e))
    except Exception:raise HTTPException(502,'Investigation could not resume. Inspect its persisted checkpoint status; no action was executed.')

@app.post('/api/{scenario}/proposals/{id}/approve')
def approval(scenario:str,id:str): return approve(store_for(scenario),id)

@app.post('/api/{scenario}/proposals/{id}/execute')
def execution(scenario:str,id:str): return execute(store_for(scenario),id)

@app.post('/api/{scenario}/session')
def session(scenario:str):
    s=store_for(scenario);id=str(uuid4())
    s.put({'id':id,'kind':'Session','title':'Investigation session','at':now()})
    return {'session_id':id,'lessons':s.lessons()}

@app.post('/api/{scenario}/state-change')
def state_change(scenario:str): return change_state(store_for(scenario))

@app.post('/api/{scenario}/recur')
def recurrence(scenario:str): return recur(store_for(scenario))

@app.post('/api/{scenario}/reset')
def reset(scenario:str):
    s=store_for(scenario)
    with s.db.connection.lock(s.name+':mutation',timeout=20,blocking_timeout=5): s.reset()
    return {'status':'reset'}

@app.get('/api/{scenario}/evidence/{id}')
def evidence(scenario:str,id:str):
    node=store_for(scenario).get(id)
    if not node: raise HTTPException(404,'Evidence record not found')
    return node

# Proof Lab uses separate graphs; all action authority stays in the same engine.
from .lab import Configuration, lab_store, snapshot as lab_snapshot, configure as lab_configure

@app.get('/api/lab/{lab_id}')
def laboratory(lab_id:UUID):return lab_snapshot(lab_store(lab_id))

@app.post('/api/lab/{lab_id}/configure')
def configure_laboratory(lab_id:UUID,body:Configuration):return lab_configure(lab_store(lab_id),body)

@app.post('/api/lab/{lab_id}/investigate')
def investigate_laboratory(lab_id:UUID):
    return run_workflow(lab_store(lab_id),'Investigate the judge-configured synthetic incident.',False)

@app.post('/api/lab/{lab_id}/proposals')
def propose_laboratory(lab_id:UUID,body:Proposal):
    s=lab_store(lab_id);sid=str(body.session_id)
    s.put({'id':sid,'kind':'Session','title':'Proof Lab session','at':now()})
    return propose(s,body.action,sid,body.run_id)

@app.post('/api/lab/{lab_id}/proposals/{id}/approve')
def approve_laboratory(lab_id:UUID,id:str):return approve(lab_store(lab_id),id)

@app.post('/api/lab/{lab_id}/proposals/{id}/execute')
def execute_laboratory(lab_id:UUID,id:str):return execute(lab_store(lab_id),id)

@app.post('/api/lab/{lab_id}/reset')
def reset_laboratory(lab_id:UUID):
    s=lab_store(lab_id)
    with s.db.connection.lock(s.name+':mutation',timeout=20,blocking_timeout=5):s.reset()
    return lab_snapshot(s)

DIST=Path(__file__).resolve().parent.parent/'frontend'/'dist'
if DIST.exists():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
    @app.get('/')
    def index(): return FileResponse(DIST/'index.html')
