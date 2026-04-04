def test_fraud_ensemble_basic(tmp_path):
    from app.services.fraud.ensemble import FraudEnsemble

    model_path = str(tmp_path / 'fraud_ensemble.pkl')
    fe = FraudEnsemble(model_path=model_path)

    # Train a small model for unit test speed
    fe.train_on_synthetic(n_samples=1000, save=True)

    normal = {
        'location_score': 10.0,
        'collusion_score': 5.0,
        'image_prob': 0.05,
        'isolation_score': 10.0,
        'claimed_ratio': 0.5,
        'event_count': 1,
    }

    fraud = {
        'location_score': 80.0,
        'collusion_score': 80.0,
        'image_prob': 0.8,
        'isolation_score': 80.0,
        'claimed_ratio': 3.0,
        'event_count': 5,
    }

    p_normal = fe.predict_proba(normal)
    p_fraud = fe.predict_proba(fraud)

    assert 0.0 <= p_normal < 0.5
    assert p_fraud > 0.6
