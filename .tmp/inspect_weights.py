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

print('Returned fraud_score:', result['fraud_score'])
print('Action:', result['action'])
print('\nDetector results raw:')
for r in result['detector_results']:
    print(r)

# Compute weighted aggregation locally from the detector_results
weights = {
    "LocationSpoofingDetector": 0.20,
    "CollusionRingDetector": 0.25,
    "ImageFraudDetector": 0.20,
    "NLPFraudDetector": 0.15,
    "TemporalFraudDetector": 0.20,
}

total_score = 0.0
total_weight = 0.0
for r in result['detector_results']:
    name = r.get('detector_name')
    score = int(r.get('fraud_score', 0))
    w = weights.get(name, 0.15)
    print(f"detector={name}, score={score}, weight={w}")
    total_score += score * w
    total_weight += w

print('total_score', total_score)
print('total_weight', total_weight)
print('computed_final_score', int(total_score/total_weight) if total_weight>0 else 0)

# Also show any_reject
any_reject = any(str(r.get('action','')).upper()=='REJECT' for r in result['detector_results'])
print('any_reject', any_reject)
