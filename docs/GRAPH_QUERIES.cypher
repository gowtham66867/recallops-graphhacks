// RecallOps' central queries. Entity scalar fields are serialized in data;
// relationships are native FalkorDB edges. IDs and query values are parameters.

// 1. Bound the blast radius (up to four dependency hops).
// $id = 'checkout'
MATCH p=(a:Entity {id:$id})-[:DEPENDS_ON*1..4]->(b:Entity)
RETURN b.data, length(p)
LIMIT 30;

// 2. Retrieve connected incident history and its original observations.
// $id = 'current'
MATCH (c:Entity {id:$id})-[:AFFECTS]->(s:Entity)
  <-[:AFFECTS]-(i:Entity)-[:ATTEMPTED]->(a:Entity)
  -[:RESULTED_IN]->(o:Entity)-[:SUPPORTED_BY]->(src:Entity)
RETURN i.data,a.data,o.data,src.data
ORDER BY a.id
LIMIT 30;

// 3. Connect the current incident to deployment and migration conditions.
// $id = 'current'; $kind = 'Migration'
MATCH (i:Entity {id:$id})-[:AFFECTS]->(s:Entity)
  <-[:DEPLOYED_TO]-(d:Entity)-[:INTRODUCED]->(m:Entity)
WHERE m.kind=$kind
RETURN i.data,d.data,m.data
LIMIT 1;

// 4. Recall conditional outcome memory for the affected service.
// $id = 'checkout'; $kind = 'Lesson'
MATCH (l:Entity)-[:APPLIES_TO]->(s:Entity {id:$id})
WHERE l.kind=$kind
RETURN l.data
ORDER BY l.id DESC
LIMIT 20;

// 5. Inspect durable checkpoints for an investigation.
// $id = a recorded run ID
MATCH (r:Entity {id:$id})-[:CHECKPOINTED]->(c:Entity)
RETURN c.id,c.data
LIMIT 5;

// The simulator's atomic multi-record write is in backend/engine.py::execute.
// The context experiment's disposable-graph edge removal is in backend/ablation.py.
