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
        "city": "Mumbai",
        "platform": "Zomato",
        "experience_days": 120,
        "avg_daily_income": 600,
        "historical_claim_rate": 0.05,
        "pincode": "400001",
        "location_density": 0.9,
        "platform_volatility": 0.3,
    }

    r = client.post("/api/calculate-premium", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "ok"

    assert "forecast_adjustment_pct" in data
    adj = data["forecast_adjustment_pct"]
    assert isinstance(adj, float) or isinstance(adj, int)
    assert -0.16 <= float(adj) <= 0.16

    assert "risk" in data and "premium" in data
    risk = data["risk"]
    premium = data["premium"]

    assert "risk_score" in risk
    assert isinstance(risk["risk_score"], (int, float))

    assert "weekly_premium" in premium
    wp = premium["weekly_premium"]
    assert isinstance(wp, int)
    assert 49 <= wp <= 99
