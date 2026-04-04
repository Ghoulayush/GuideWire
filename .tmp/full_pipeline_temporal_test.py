from app.services.fraud import FraudEngine
from datetime import datetime, timedelta

engine = FraudEngine()

# Create claim with temporal fraud pattern (rapid succession)
test_claim = {
    'gps_history': [(19.0760, 72.8777)],
    'review_text': 'This is a test review',
    'worker_history': {
        'claim_frequency': 10,
        'experience_days': 30
    }
}

# Add temporal claim history
test_claim['claim_history'] = []
for i in range(15):
    d = datetime.now() - timedelta(hours=i*2)
    test_claim['claim_history'].append({
        'date': d,
        'amount': 500,
        'hour': d.hour,
        'is_weekend': False,
        'days_since_last': 0,
        'severity': 3
    })

result = engine.evaluate_claim(test_claim)

print('=' * 50)
print('FULL FRAUD PIPELINE (Layers 1-6)')
print('=' * 50)
print(f"Final Fraud Score: {result['fraud_score']}/100")
print(f"Action: {result['action']}")
print(f"Confidence: {result['confidence']}%")
print(f"Final Decision: {result['final_decision']}")
print('\nDetectors Run:')
for r in result['detector_results']:
    if isinstance(r, dict):
        dn = r.get('detector_name', 'unknown')
        ds = r.get('fraud_score', 0)
        da = r.get('action', 'UNKNOWN')
    else:
        dn = getattr(r, 'detector_name', 'unknown')
        ds = getattr(r, 'fraud_score', 0)
        da = getattr(r, 'action', 'UNKNOWN')
    print(f"  - {dn}: score={ds}, action={da}")
