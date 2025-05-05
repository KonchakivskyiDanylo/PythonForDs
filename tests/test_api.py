import json
import server  # <— ось цього бракує
from server import app

def test_homepage():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200

def test_predict_unauthorized():
    client = app.test_client()
    response = client.post("/predict", json={"token": "invalid"})
    assert response.status_code == 500

def test_predict_no_region(monkeypatch):
    server.API_TOKEN = "test-token"
    client = app.test_client()
    monkeypatch.setenv("API_TOKEN", "test-token")
    response = client.post("/predict", json={"token": "test-token"})
    assert response.status_code in [200, 404]

def test_alarms():
    client = app.test_client()
    response = client.get("/alarms")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
