import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import ai_service as ai

client = TestClient(app)


@pytest.fixture(autouse=True)
def fast_settings():
    ai.settings.ai_delay, ai.settings.ai_timeout = 0.3, 2.0
    yield


def test_summarise_returns_result_not_coroutine():
    r = client.post("/summarise", json={"text": "photosynthesis"})
    assert r.status_code == 200
    assert isinstance(r.json()["summary"], str)


def test_timeout_returns_504():
    ai.settings.ai_delay, ai.settings.ai_timeout = 1.0, 0.2   # AI slower than the limit
    r = client.post("/summarise", json={"text": "photosynthesis"})
    assert r.status_code == 504
    assert "too long" in r.json()["detail"]


def test_temporary_failure_returns_503():
    r = client.post("/summarise", json={"text": "please fail"})
    assert r.status_code == 503


def test_concurrent_is_faster_than_sequential():
    c = client.post("/study-pack", json={"text": "cells"}).json()
    s = client.post("/study-pack-sequential", json={"text": "cells"}).json()
    assert c["seconds"] < s["seconds"]
    assert s["seconds"] >= 0.9          # ~3 x 0.3s
    assert c["seconds"] < 0.6           # ~1 x 0.3s
