from fastapi.testclient import TestClient
from costwatch.main import app
 
 
def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
 
 
def test_alert_is_accepted(monkeypatch):
    monkeypatch.setattr("costwatch.main.investigator.run", lambda payload: None)
    r = TestClient(app).post("/alert", json={"alerts": [{"labels": {"alertname": "Test"}}]})
    assert r.status_code == 200
    assert r.json()["alerts"] == 1
