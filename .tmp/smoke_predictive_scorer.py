from app.services.fraud.predictive_scorer import PredictiveFraudScorer
from app.services.fraud.base_detector import FraudResult, FraudAction

ps = PredictiveFraudScorer()

r1 = FraudResult(fraud_score=40, action=FraudAction.REVIEW, reason='loc anomaly', confidence=70, detector_name='LocationSpoofingDetector')
r2 = FraudResult(fraud_score=60, action=FraudAction.REVIEW, reason='collusion cluster', confidence=80, detector_name='CollusionRingDetector')
r3 = FraudResult(fraud_score=20, action=FraudAction.APPROVE, reason='image ok', confidence=90, detector_name='ImageFraudDetector')
r4 = FraudResult(fraud_score=50, action=FraudAction.REVIEW, reason='nlp suspicious', confidence=75, detector_name='NLPFraudDetector')

res = ps.predict([r1, r2, r3, r4], {'claim_frequency':2,'claim_amount_ratio':0.3,'days_since_last_claim':10,'experience_days':100,'weekend_claim_ratio':0.2})
print(res.model_dump() if hasattr(res, 'model_dump') else res)
