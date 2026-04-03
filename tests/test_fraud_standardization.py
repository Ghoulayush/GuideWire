"""
Test that ALL detectors return the SAME format
"""

from app.services.fraud.location_detector import LocationSpoofingDetector
from app.services.fraud.collusion_detector import CollusionRingDetector
from app.services.fraud.image_detector import ImageFraudDetector


def test_all_detectors_have_standard_output():
    """Verify every detector returns the expected format"""

    detectors = [
        ("LocationSpoofingDetector", LocationSpoofingDetector()),
        ("CollusionRingDetector", CollusionRingDetector()),
        ("ImageFraudDetector", ImageFraudDetector()),
    ]

    expected_keys = {'fraud_score', 'action', 'reason', 'confidence'}

    for name, detector in detectors:
        print(f"\nTesting {name}...")

        # Each detector needs its own test input
        if name == "LocationSpoofingDetector":
            result = detector.detect([(19.0760, 72.8777), (19.0761, 72.8778)])
        elif name == "CollusionRingDetector":
            result = detector.detect_rings([])
        else:  # ImageFraudDetector
            result = detector.detect("test.jpg")

        # Check if result has all expected keys
        if hasattr(result, 'model_dump'):  # Pydantic model
            result_dict = result.model_dump()
        else:  # Regular dict
            result_dict = result

        missing_keys = expected_keys - set(result_dict.keys())
        assert not missing_keys, f"{name} missing keys: {missing_keys}"

        # Check value ranges
        assert 0 <= result_dict['fraud_score'] <= 100, f"{name} fraud_score out of range"
        assert result_dict['action'] in ['APPROVE', 'REVIEW', 'REJECT'], f"{name} invalid action"
        assert 0 <= result_dict['confidence'] <= 100, f"{name} confidence out of range"

        print(f"✅ {name} passed! fraud_score={result_dict['fraud_score']}, action={result_dict['action']}")

    print("\n🎉 ALL DETECTORS PASSED STANDARDIZATION!")


if __name__ == "__main__":
    test_all_detectors_have_standard_output()
