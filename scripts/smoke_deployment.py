"""Verify the protected deployment, using only the rollback-valid simulator.

Usage: .venv/bin/python -m scripts.smoke_deployment artifacts/deployment-access.txt
The access file is local, ignored, and must never be included in build uploads.
"""
import json
import sys
from pathlib import Path
import httpx


def main():
    access = dict(line.split(': ', 1) for line in Path(sys.argv[1]).read_text().splitlines() if ': ' in line)
    url = access['URL']
    with httpx.Client(base_url=url, timeout=45, follow_redirects=True) as public:
        assert public.get('/api/health').status_code == 401, 'Anonymous API access must be blocked'
    with httpx.Client(base_url=url, auth=(access['Username'], access['Password']), timeout=45,
                      headers={'Origin': url}, follow_redirects=True) as client:
        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

        health = request('GET', '/api/health')
        assert health['status'] == 'ok' and health['database'] == 'FalkorDB'
        assert not health['live_available'], 'This deployment should not contain the exposed local model key'
        page = client.get('/')
        assert page.status_code == 200 and '/assets/' in page.text
        scenarios = request('GET', '/api/scenarios')
        assert len(scenarios) == 5
        base = '/api/rollback-valid'
        request('POST', base + '/reset')
        session = request('POST', base + '/session')
        run = request('POST', base + '/investigate', json={'question': 'Deployment smoke check: verify rollback evidence.', 'live': False})
        assert run['verification']['status'] == 'passed'
        assert run['recommendation']['action'] == 'rollback'
        proposal = request('POST', base + '/proposals', json={'action': 'rollback', 'session_id': session['session_id'], 'run_id': run['run_id']})
        action_path = base + '/proposals/' + proposal['id']
        assert client.post(action_path + '/execute').status_code == 409
        request('POST', action_path + '/approve')
        outcome = request('POST', action_path + '/execute')
        assert outcome['status'] == 'succeeded'
        assert request('POST', action_path + '/execute') == outcome
        snapshot = request('GET', base + '/snapshot')
        assert snapshot['incident']['error_rate'] == .2 and len(snapshot['lessons']) == 1
        assert len(request('POST', base + '/session')['lessons']) == 1
        evidence = {'url': url, 'https_verified': True, 'anonymous_access': 401,
                    'scenarios': len(scenarios), 'run_id': run['run_id'],
                    'verification': 'passed', 'approval_required': True,
                    'execution': 'succeeded', 'idempotent': True,
                    'recovered_error_rate': .2, 'persisted_lessons': 1,
                    'live_available': False}
        Path('artifacts/deployment-smoke.json').write_text(json.dumps(evidence, indent=2) + '\n')
        print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
