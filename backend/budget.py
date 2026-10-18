"""One code-owned live-call budget shared by researcher and critic per invocation."""
import time
from contextvars import ContextVar
from openai import OpenAI

LIMITS={'model_requests':9,'evidence_tool_calls':12,'assessment_repairs':1,'deadline_seconds':120,'per_request_seconds':25,'specialists':3}
ACTIVE=ContextVar('recallops_budget',default=None)

class Budget:
    def __init__(self):self.started=time.monotonic();self.requests=0
    def check(self):
        remaining=LIMITS['deadline_seconds']-(time.monotonic()-self.started)
        if remaining<=0:raise ValueError('Shared investigation deadline exhausted. No action was authorized.')
        return remaining
    def request(self,client):
        remaining=self.check()
        if self.requests>=LIMITS['model_requests']:raise ValueError('Shared researcher and critic request budget exhausted.')
        self.requests+=1
        return client.with_options(timeout=min(LIMITS['per_request_seconds'],remaining),max_retries=0) if isinstance(client,OpenAI) else client
    def snapshot(self):return {'limits':LIMITS,'used_model_requests':self.requests,'elapsed_ms':round((time.monotonic()-self.started)*1000,1),'scope':'Per invocation including resume. SDK transport timeouts cap each network operation; this is not a hard process-kill deadline.'}
