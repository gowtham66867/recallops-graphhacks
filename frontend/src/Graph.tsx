import {useState} from 'react';
import {Maximize2,Minus,Plus,GitBranch} from 'lucide-react';
import type {Snapshot,RecordNode} from './types';
const positions:Record<string,[number,number]>={
 'current':[85,185], 'checkout':[290,185], 'deploy-current':[290,65], 'migration':[520,65], 'flag':[745,65],
 'inc-017':[85,305], 'attempt-017':[290,305], 'outcome-017':[520,305],
 'inc-021':[85,420], 'attempt-021':[290,420], 'outcome-021':[520,420],
 'payments':[520,165],'orders':[520,225],'postgres':[745,195],'inventory':[745,305],
};
const primary=new Set(Object.keys(positions));
export default function Graph({snapshot,highlight,onSelect}:{snapshot:Snapshot;highlight:string[];onSelect:(n:RecordNode)=>void}){
 const[zoom,setZoom]=useState(1);const[expanded,setExpanded]=useState(false);
 const nodes=snapshot.nodes.filter(n=>primary.has(n.id));
 const edges=snapshot.edges.filter(e=>primary.has(e.source)&&primary.has(e.target));
 return <section className={'panel graph-panel '+(expanded?'graph-expanded':'')}>
 <div className="panel-heading"><div><div className="eyebrow"><GitBranch size={13}/> CONNECTED EVIDENCE</div><h2>The path behind the decision</h2></div><button className="icon-button" onClick={()=>setExpanded(!expanded)} aria-label={expanded?'Collapse graph':'Expand graph'}><Maximize2 size={16}/></button></div>
 <div className="graph-subtitle">Actual FalkorDB relationships <span>·</span> Select a node to inspect its record</div>
 <div className="graph-canvas"><svg viewBox="0 0 850 485" role="group" aria-label="Incident evidence graph: deployment, schema, service dependencies and historical action outcomes">
 <defs><pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#d6dfd7"/></pattern><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#8faaa0"/></marker></defs>
 <rect width="850" height="485" fill="url(#dots)"/>
 <g transform={`translate(${425-425*zoom} ${240-240*zoom}) scale(${zoom})`}>
 {edges.map((e,i)=>{const [x,y]=positions[e.source];const [tx,ty]=positions[e.target];const on=highlight.includes(e.source)&&highlight.includes(e.target);const vertical=Math.abs(tx-x)<10;const d=e.source==='deploy-current'&&e.target==='flag'?`M${x+72} ${y-10} C${x+140} ${y-70} ${tx-140} ${ty-70} ${tx-73} ${ty-10}`:vertical?`M${x} ${y+24} L${tx} ${ty-24}`:`M${x+72} ${y} C${(x+tx)/2} ${y} ${(x+tx)/2} ${ty} ${tx-73} ${ty}`;return <g key={i} opacity={highlight.length&&!on?.28:1}><path d={d} fill="none" stroke={on?'#338665':'#aebeb3'} strokeWidth={on?2:1.1} markerEnd="url(#arrow)"/>{!vertical&&<text x={(x+tx)/2} y={(y+ty)/2-9} textAnchor="middle" className="edge-label">{e.label.replaceAll('_',' ').toLowerCase()}</text>}</g>})}
 {nodes.map(n=>{const [x,y]=positions[n.id];const on=highlight.includes(n.id);const tone=n.kind==='Outcome'?(n.status==='failed'?'rose':'green'):n.kind==='Migration'?'amber':n.kind==='Incident'?'rose':n.kind==='Deployment'?'blue':'green';return <g key={n.id} transform={`translate(${x-72} ${y-23})`} className={'graph-node '+tone+(on?' highlighted':'')} opacity={highlight.length&&!on?.42:1} tabIndex={0} role="button" aria-label={`Inspect ${n.title}`} onClick={()=>onSelect(n)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(n)}}}>
 <title>{n.title}</title><rect width="144" height="47" rx="7"/><circle cx="13" cy="15" r="3"/><text x="23" y="18" className="node-kind">{n.kind==='Incident'?(n.code as string)||'INCIDENT':n.kind.replace(/([A-Z])/g,' $1').trim().toUpperCase()}</text><text x="12" y="35" className="node-name">{n.title.length>21?n.title.slice(0,20)+'…':n.title}</text></g>})}
 </g></svg><div className="graph-controls"><button aria-label="Zoom out" onClick={()=>setZoom(Math.max(.7,zoom-.15))}><Minus size={14}/></button><span>{Math.round(zoom*100)}%</span><button aria-label="Zoom in" onClick={()=>setZoom(Math.min(1.6,zoom+.15))}><Plus size={14}/></button></div></div>
 <div className="graph-legend"><span><i className="green-dot"/> Service / action</span><span><i className="blue-dot"/> Deployment</span><span><i className="amber-dot"/> Schema</span><span><i className="rose-dot"/> Incident</span><span className="graph-count">{nodes.length} nodes · {edges.length} edges</span></div>
 </section>
}
