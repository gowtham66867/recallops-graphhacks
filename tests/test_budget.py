from types import SimpleNamespace
import pytest
from backend.budget import Budget,LIMITS


def test_request_budget_is_shared_and_exhausts():
    budget=Budget();client=SimpleNamespace()
    for i in range(LIMITS['model_requests']):assert budget.request(client) is client
    with pytest.raises(ValueError,match='request budget'):budget.request(client)
    assert budget.snapshot()['used_model_requests']==9


def test_expired_deadline_stops_before_request(monkeypatch):
    import backend.budget as module
    b=Budget();monkeypatch.setattr(module.time,'monotonic',lambda:b.started+121)
    with pytest.raises(ValueError,match='deadline'):b.request(SimpleNamespace())
    assert b.requests==0
