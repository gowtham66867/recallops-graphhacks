from uuid import uuid4
import pytest
from backend.store import Store
from backend.ablation import compare_history
from backend.evidence import current_digest


@pytest.mark.parametrize('scenario,action,expected',[('checkout','restart','contradicted'),('rollback-valid','rollback','supported')])
def test_context_ablation_changes_policy_without_mutating_source(scenario,action,expected):
    store=Store(scenario,prefix='ablation_test_'+uuid4().hex);store.seed()
    try:
        before=current_digest(store)
        graphs_before=set(store.db.connection.execute_command('GRAPH.LIST'))
        result=compare_history(store)
        row=next(r for r in result['comparisons'] if r['action']==action)
        assert row['with_history']==expected and row['without_history']=='unknown'
        assert row['changed'] and result['historical_outcomes']==2
        assert current_digest(store)==before==result['source_digest']
        assert set(store.db.connection.execute_command('GRAPH.LIST'))==graphs_before
        assert result['original_graph_modified'] is False
    finally:store.graph.delete()
