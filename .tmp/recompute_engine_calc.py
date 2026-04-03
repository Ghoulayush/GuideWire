from app.services.fraud import FraudEngine
from datetime import datetime, timedelta

engine = FraudEngine()

# Build detectors list by calling detectors directly
detector_results = []
# Location
try:
    loc = engine.location_detector.detect([(19.0760, 72.8777)])
    detector_results.append(loc)
except Exception as e:
    print('loc error', e)

# NLP
try:
    nlp = getattr(engine, 'nlp_detector', None)
    if nlp is not None:
        nlp_res = nlp.detect(review_text='This is a test review', delivery_data={})
        detector_results.append(nlp_res)
except Exception as e:
    print('nlp error', e)

# Temporal
try:
    temp = getattr(engine, 'temporal_detector', None)
    if temp is not None:
        claim_history = []
        for i in range(15):
            d = datetime.now() - timedelta(hours=i*2)
            claim_history.append({
                'date': d,
                'amount': 500,
                'hour': d.hour,
                'is_weekend': False,
                'days_since_last': 0,
                'severity': 3
            })
        temp_res = temp.detect('worker-1', claim_history)
        detector_results.append(temp_res)
except Exception as e:
    print('temp error', e)

print('Raw detector objects:')
for r in detector_results:
    print(type(r), getattr(r, 'detector_name', None), getattr(r, 'fraud_score', None), getattr(r, 'action', None))

# Apply engine's weighted aggregation exactly
weights = {
    "LocationSpoofingDetector": 0.20,
    "CollusionRingDetector": 0.25,
    "ImageFraudDetector": 0.20,
    "NLPFraudDetector": 0.15,
    "TemporalFraudDetector": 0.20,
}

total_score = 0.0
total_weight = 0.0
for r in detector_results:
    if isinstance(r, dict):
        name = r.get('detector_name')
        try:
            score = int(r.get('fraud_score', 0))
        except Exception:
            score = 0
    else:
        name = getattr(r, 'detector_name', None)
        try:
            score = int(getattr(r, 'fraud_score', 0))
        except Exception:
            score = 0
    w = weights.get(name, 0.15)
    print('name:', name, 'score:', score, 'w:', w)
    total_score += score * w
    total_weight += w

final_score = int(total_score / total_weight) if total_weight > 0 else 0
print('computed final_score:', final_score)

any_reject = any((getattr(r, 'action').value == 'REJECT') if (not isinstance(r, dict) and hasattr(r, 'action')) else (str(r.get('action','')).upper()=='REJECT') for r in detector_results)
print('any_reject:', any_reject)
if any_reject:
    final_score = max(final_score, 60)
print('final_score after boost:', final_score)
