from fastapi.testclient import TestClient

from app.main import app
from app.services.ml_risk import GigShieldRiskModel
from app.services.fraud.advanced_detection import detect_advanced_signals


client = TestClient(app)


def test_predict_risk_handles_malformed_payload():
    model = GigShieldRiskModel()

    payload = {
        "city": None,
        "platform": 123,
        "experience_days": -500,
        "avg_daily_income": "nan",
        "historical_claim_rate": "2.5",
        "weather_forecast_risk": 9999,
        "current_aqi": -10,
    }

    result = model.predict_risk(payload)
    score = float(result["risk_score"])

    assert 0.0 <= score <= 100.0
    assert result["risk_band"] in {"Low", "Medium", "High"}
    assert result["confidence_band"] in {"low", "medium", "high"}
    assert isinstance(result.get("reason_codes"), list)
    assert result.get("recommended_action") in {
        "AUTO_APPROVE",
        "REVIEW",
        "REVIEW_PRIORITY",
    }


def test_advanced_detection_flags_suspicious_pattern():
    claim_data = {
        "gps_history": [
            {"lat": 19.0760, "lon": 72.8777, "ts": 1700000000},
            {"lat": 28.6139, "lon": 77.2090, "ts": 1700000200},
        ],
        "claimed_weather": {"rain_mm": 90},
        "actual_weather": {"rain_mm": 1},
        "claims_in_area": [
            {"timestamp": "2026-04-17T10:00:00"},
            {"timestamp": "2026-04-17T10:10:00"},
            {"timestamp": "2026-04-17T10:20:00"},
            {"timestamp": "2026-04-17T10:30:00"},
            {"timestamp": "2026-04-17T10:40:00"},
        ],
        "historical_validation": {"matches_pattern": False},
    }

    result = detect_advanced_signals(claim_data)

    assert result["fraud_score"] >= 40
    assert result["action"] in {"REVIEW", "REJECT"}
    assert "detector_name" in result


def test_health_endpoint_exposes_model_diagnostics():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert "model_metadata" in data
    assert "model_runtime_diagnostics" in data
    assert "external_signals_mode" in data
