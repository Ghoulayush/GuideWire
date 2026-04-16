from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "ml_model_loaded" in data


def test_calculate_premium_basic():
    payload = {
        "worker_id": "test-premium-001",
        "name": "Premium Test",
        "city": "Mumbai",
        "pincode": "400001",
        "platform": "Zomato",
        "avg_daily_income": 600,
    }

    r = client.post("/workers/onboard", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()

    assert "risk" in data and "policy" in data
    risk = data["risk"]
    policy = data["policy"]

    assert "risk_score" in risk
    assert isinstance(risk["risk_score"], (int, float))

    assert "weekly_premium" in policy
    wp = policy["weekly_premium"]
    assert isinstance(wp, (int, float))
    assert 49 <= wp <= 99


def test_trigger_event_pipeline():
    onboard = {
        "worker_id": "test-event-001",
        "name": "Event Test",
        "city": "Delhi",
        "pincode": "110001",
        "platform": "Swiggy",
        "avg_daily_income": 700,
    }
    r_onboard = client.post("/workers/onboard", json=onboard)
    assert r_onboard.status_code == 200, r_onboard.text

    event_payload = {
        "worker_id": onboard["worker_id"],
        "disruption_type": "environmental",
        "severity": 4,
        "description": "Heavy rain in coverage area",
    }
    r_event = client.post("/events/trigger", json=event_payload)
    assert r_event.status_code == 200, r_event.text
    data = r_event.json()

    assert "triggered" in data
    assert "message" in data
    assert data["event"]["worker_id"] == onboard["worker_id"]
