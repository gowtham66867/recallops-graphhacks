export type RecordNode={id:string;kind:string;title:string;[key:string]:unknown};
export type Edge={source:string;target:string;label:string};
export type Incident=RecordNode&{status:string;revision:number;error_rate:number;signature:string;flag_enabled:boolean;schema_known:boolean};
export type Snapshot={nodes:RecordNode[];edges:Edge[];incident:Incident;lessons:RecordNode[];attempts:RecordNode[];scenario:string};
export type Check={action:string;title:string;command:string;description:string;status:'supported'|'contradicted'|'unknown';reason:string;evidence:string[];preconditions:string[]};
export type Investigation={checks:Check[];recommendation:Check|null;revision:number;lessons:RecordNode[];dependencies:{service:RecordNode;hops:number}[];history:unknown[];summary:string;mode:string;trace:{tool:string;description:string;ms:number;records:number}[];elapsed_ms:number;run_id:string;state_hash:string;verification:{status:string;issues:string[];evidence_count:number;source_count:number};critic:{kind:string;accepted:boolean;issues:string[]};counterfactuals:{action:string;title:string;applicability:string;verdict:string;reason:string;predicted_error_rate:number|null}[];plan:{role:string;task:string;tools:string[]}[];workflow:{checkpoint_count:number;phase:string;resume_count:number;durable:boolean}};
export type Scenario={id:string;name:string;description:string};
