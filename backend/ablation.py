"""A controlled graph-context experiment, isolated from the user's incident."""
from uuid import uuid4
from .store import Store, now
from .engine import check_actions
from .evidence import digest


def compare_history(store):
    facts = store.fact_snapshot()
    sandbox = Store(store.scenario, prefix='ablation_' + uuid4().hex)
    try:
        for node in facts['nodes']:
            sandbox.put(node)
        for edge in facts['edges']:
            sandbox.link(edge['source'], edge['label'], edge['target'])
        before = check_actions(sandbox)
        history_count = len(sandbox.history())
        lesson_count = len(sandbox.lessons())
        sandbox.query('MATCH (i:Entity)-[r:AFFECTS]->(:Entity {id:$service}) WHERE i.id <> $current DELETE r',
                      {'service': 'checkout', 'current': 'current'})
        sandbox.query('MATCH (l:Entity)-[r:APPLIES_TO]->(:Entity {id:$service}) WHERE l.kind=$kind DELETE r',
                      {'service': 'checkout', 'kind': 'Lesson'})
        after = {row['action']: row for row in check_actions(sandbox)}
        return {
            'measured_at': now(), 'source_digest': digest(facts),
            'mode': 'deterministic graph-context ablation',
            'historical_outcomes': history_count, 'conditional_lessons': lesson_count,
            'original_graph_modified': False,
            'scope': 'Same factual snapshot and policy. Only historical AFFECTS and lesson APPLIES_TO edges are removed in a disposable FalkorDB graph. Current deployment evidence stays intact.',
            'limitation': 'This measures the effect of retrieved graph context on fixed rules. It is not an LLM accuracy comparison.',
            'comparisons': [{'action': row['action'], 'title': row['title'],
                             'with_history': row['status'], 'without_history': after[row['action']]['status'],
                             'with_reason': row['reason'], 'without_reason': after[row['action']]['reason'],
                             'changed': row['status'] != after[row['action']]['status']}
                            for row in before]
        }
    finally:
        sandbox.graph.delete()
