import {CheckCircle2,GitBranch,ShieldCheck,TriangleAlert} from 'lucide-react';
import type {Investigation} from './types';
export default function RunProof({result}:{result:Investigation|null}){
 if(!result?.verification)return null;
 const passed=result.verification.status==='passed';
 return <section className="panel deliberation-panel">
 <div className="panel-heading"><div><div className="eyebrow"><GitBranch size={13}/> INVESTIGATE → COMPARE → VERIFY</div><h2>Compare the alternatives before acting.</h2></div><span className={'pill '+(passed?'green':'red')}>{passed?<ShieldCheck size={12}/>:<TriangleAlert size={12}/>} {passed?'EVIDENCE VERIFIED':'HANDOFF BLOCKED'}</span></div>
 <p className="forecast-disclosure">Forecasts below are dry-runs of simulator rules. They are predictions, not observed recoveries.</p>
 <div className="forecast-grid">{result.counterfactuals.map(c=><div className={'forecast-card '+c.verdict} key={c.action}><span className="eyebrow">{c.applicability.toUpperCase()}</span><strong>{c.title}</strong><div>{c.predicted_error_rate!==null?<><span className="forecast-value">{c.predicted_error_rate}%</span><span> predicted error rate</span></>:<span className="forecast-no-action">{c.verdict==='blocked'?'Not eligible to simulate':'Insufficient evidence'}</span>}</div><p>{c.reason}</p></div>)}</div>
 <div className="verification-strip"><span><CheckCircle2 size={14}/>{result.verification.evidence_count} records · {result.verification.source_count} original sources checked</span><span>{result.critic.kind==='independent model critic'?'Independent model critic':'Deterministic evidence verifier'} · {result.critic.accepted?'passed':'blocked'}</span><span>{result.workflow.checkpoint_count} durable checkpoints</span></div>
 {!passed&&<div className="verification-issues" role="alert">{result.verification.issues.map((s,i)=><p key={i}><TriangleAlert size={12}/>{s}</p>)}</div>}
 <details className="workflow-details"><summary>Inspect the investigation handoff <span className="mono">{result.run_id.slice(0,16)}</span></summary><div className="workflow-stages">{result.plan.map(p=><div key={p.role}><strong>{p.role}</strong><p>{p.task}</p></div>)}</div><p className="workflow-footnote">Three independent read-only specialists run concurrently. Their findings join before synthesis and verification. {result.mode==='live'?'Live mode adds a tool-calling researcher and a separately prompted model critic.':'This run used deterministic specialists; no model agents were called.'} The approved action is bound to the verified evidence state. Saved stages can resume after interruption if that state is unchanged.</p></details>
 </section>
}
