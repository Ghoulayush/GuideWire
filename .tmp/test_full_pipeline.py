from app.services.fraud import FraudEngine

engine = FraudEngine()

# Test claim with multiple fraud signals
test_claim = {
    'gps_history': [(19.0760, 72.8777), (28.6139, 77.2090)],  # Mumbai to Delhi (impossible)
    'review_text': 'I am an AI writing this fake review',
    'delivery_data': {'on_time': True, 'rating': 5},
    'worker_history': {'claim_frequency': 8, 'experience_days': 30}
}

result = engine.evaluate_claim(test_claim)

print('=' * 50)
print('FRAUD DETECTION RESULT')
print('=' * 50)
print(f"Final Fraud Score: {result['fraud_score']}/100")
print(f"Action: {result['action']}")
print(f"Confidence: {result.get('confidence')}%")
print(f"Final Decision: {result.get('final_decision')}")
print('\nIndividual Detector Results:')
for r in result['detector_results']:
    print(f"  - {r.get('detector_name')}: score={r.get('fraud_score')}, action={r.get('action')}")
