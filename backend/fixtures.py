"""Inspectable synthetic scenario inputs. Expected decisions live in tests, not agent prompts."""
SCENARIOS = {
    'checkout': {'name': 'Checkout regression', 'description': 'A migration invalidates yesterday’s rollback.', 'signature': 'feature_contract', 'schema': 3, 'rollback_schema': 2, 'flag': True, 'pool': False, 'error_rate': 18.4, 'known': True},
    'rollback-valid': {'name': 'Compatible rollback', 'description': 'Same symptom. Different schema. Different decision.', 'signature': 'release_regression', 'schema': 2, 'rollback_schema': 2, 'flag': False, 'pool': False, 'error_rate': 12.6, 'known': True},
    'unknown': {'name': 'Insufficient evidence', 'description': 'Missing schema telemetry means no assumed compatibility.', 'signature': 'unclassified', 'schema': -1, 'rollback_schema': 2, 'flag': False, 'pool': False, 'error_rate': 9.2, 'known': False},
    'pool': {'name': 'Connection exhaustion', 'description': 'The feature flag cannot fix an unrelated bottleneck.', 'signature': 'pool_exhaustion', 'schema': 3, 'rollback_schema': 2, 'flag': True, 'pool': True, 'error_rate': 22.1, 'known': True},
    'dependency': {'name': 'Dependency changed', 'description': 'Checkout now depends on inventory, expanding the impact path.', 'signature': 'feature_contract', 'schema': 3, 'rollback_schema': 2, 'flag': True, 'pool': False, 'error_rate': 18.4, 'known': True, 'extra_dependency': True},
}
ACTIONS = {
    'disable_flag': {'title': 'Disable express checkout', 'command': 'feature.set express_checkout_v2=false', 'description': 'Route checkout through the stable code path. No deployment required.'},
    'rollback': {'title': 'Roll back checkout', 'command': 'deployment.rollback checkout --to v2.7.0', 'description': 'Restore the previous application version, only if the schema is compatible.'},
    'restart': {'title': 'Restart checkout', 'command': 'service.restart checkout', 'description': 'Recycle checkout workers without changing the deployment.'},
    'scale_pool': {'title': 'Increase connection pool', 'command': 'pool.resize checkout --capacity 80', 'description': 'Increase simulator pool capacity when saturation is observed.'},
}
SERVICES = [('storefront', 'Storefront', 'Experience'), ('checkout', 'Checkout API', 'Commerce'), ('payments', 'Payments', 'Commerce'), ('orders', 'Orders', 'Commerce'), ('inventory', 'Inventory', 'Platform'), ('postgres', 'PostgreSQL', 'Platform')]
